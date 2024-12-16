import pathlib

import tempdir
from termcolor import colored

from bigbuild import RepoInstance
from bigbuild.utils import load_bigbuild_dataset, progress
from bigbuild.utils.repo import fake_git_diff, get_repo


def sanitize(response: str, instance: RepoInstance):
    """
    Processes a response string to extract and organize edits associated with
    build file listings. It identifies and refines the edits based on
    filename extraction from the response, prioritizing by filename source
    reliability. The function returns a dictionary of build files with their
    corresponding edited content.

    Args:
        response (str): The response containing potential build file listings
                        and edits.
        instance (RepoInstance): An instance containing information about the
                                 repository, including available build files.

    Returns:
        dict: A dictionary mapping each build file name to its corresponding
              edited content.
    """
    output = []
    lines = response.splitlines(keepends=True)
    edits = []
    saw_fname = None
    fname = None
    fname_source = None
    new_lines = []
    for i, line in enumerate(lines):
        if line.startswith("```") or line.startswith("```"):
            if fname is not None:
                # ending an existing block
                saw_fname = None
                edits.append((fname, fname_source, new_lines))
                fname = None
                fname_source = None
                new_lines = []
                continue

            # fname==None ... starting a new block
            if i > 0:
                fname_source = "block"
                fname = lines[i - 1].strip()
                fname = fname.strip("*")  # handle **filename.py**
                fname = fname.rstrip(":")
                fname = fname.strip("`")
                fname = fname.lstrip("#")
                fname = fname.strip()
                if len(fname) > 250:
                    fname = ""

                # Did gpt prepend a bogus dir? It especially likes to
                # include the path/to prefix from the one-shot example in
                # the prompt.
                if (
                    fname
                    and fname not in instance.build_files
                    and pathlib.Path(fname).name in instance.build_files
                ):
                    fname = pathlib.Path(fname).name
            if not fname:  # blank line? or ``` was on first line i==0
                if saw_fname:
                    fname = saw_fname
                    fname_source = "saw"
                elif len(instance.build_files) == 1:
                    fname = instance.build_files[0]
                    fname_source = "chat"
                else:
                    # TODO: sense which file it is by diff size
                    print(
                        colored(
                            "No filename provided before ``` in file listing", "red"
                        )
                    )
        elif fname is not None:
            new_lines.append(line)
        else:
            for word in line.strip().split():
                word = word.rstrip(".:,;!")
                for build_file in instance.build_files:
                    quoted_chat_file = f"`{build_file}`"
                    if word == quoted_chat_file:
                        saw_fname = build_file
            output.append(line)
    if fname:
        edits.append((fname, fname_source, new_lines))

    seen = set()
    refined_edits = []
    # process from most reliable filename, to least reliable
    for source in ("block", "saw", "chat"):
        for fname, fname_source, new_lines in edits:
            if fname_source != source:
                continue
            # if a higher priority source already edited the file, skip
            if fname in seen:
                continue

            seen.add(fname)
            refined_edits.append((fname, fname_source, new_lines))

    build_files = {}
    for build_file in instance.build_files:
        # find the build file with the highest probability
        for fname, fname_source, new_lines in refined_edits:
            if build_file in fname or pathlib.Path(fname).name == build_file:
                build_files[build_file] = "".join(new_lines)
                break
    return build_files


def original_build_files(instance: RepoInstance, project_root: pathlib.Path | None):
    if not project_root:
        with tempdir.TempDir() as temp_dir:
            project_root = pathlib.Path(temp_dir) / instance.instance_id
            print(
                colored(
                    f"Downloading {instance.instance_id} to {project_root}", "green"
                )
            )
            get_repo(instance, project_root)
            return {
                file: (project_root / file).read_text() for file in instance.build_files
            }
    else:
        return {
            file: (project_root / file).read_text() for file in instance.build_files
        }


def make_patch(
    new_build_files: dict[str, str],
    instance: RepoInstance,
    project_root: pathlib.Path | None,
):
    # get old build files
    old_build_files = original_build_files(instance, project_root)
    # if key is not in new_build_files, add it
    for file in old_build_files:
        if file not in new_build_files:
            new_build_files[file] = old_build_files[file]
            print(
                colored(
                    f"build file {file} is not in the new build files. Adding it from the original build files.",
                    "yellow",
                )
            )

    diff_pair = {
        file: (old_build_files[file], new_build_files[file])
        for file in new_build_files.keys()
    }

    patch = fake_git_diff("playground", diff_pair)
    return patch


def main(
    result_dir: str,
    dataset_name_or_path: str = "data/regular.jsonl-Mini",
    repo_cache: str | None = None,
):
    dataset = load_bigbuild_dataset(dataset_name_or_path)
    result_dir: pathlib.Path = pathlib.Path(result_dir)
    with progress("Sanitizing") as p:
        for instance in p.track(dataset):
            print(
                colored(
                    f"Sanitizing {instance.language.lower()}/{instance.instance_id}",
                    "green",
                )
            )
            instance_id: str = instance.instance_id
            raw_response_path: pathlib.Path = (
                result_dir / instance.language.lower() / instance_id / "raw_response.md"
            )
            if (
                not raw_response_path.exists()
                or len(raw_response_path.read_text().strip()) == 0
            ):
                print(
                    colored(
                        f"Empty response for {instance_id} in {raw_response_path}",
                        "yellow",
                    )
                )
                (
                    result_dir / instance.language.lower() / instance_id / "patch.diff"
                ).write_text("")
                continue
            response: str = raw_response_path.read_text()
            project_root = (
                pathlib.Path(repo_cache) / instance.language.lower() / instance_id
                if repo_cache
                and (
                    pathlib.Path(repo_cache) / instance.language.lower() / instance_id
                ).exists()
                else None
            )
            patch = make_patch(sanitize(response, instance), instance, project_root)
            (
                result_dir / instance.language.lower() / instance_id / "patch.diff"
            ).write_text(patch)


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
