import glob
import json
import pathlib
from datetime import datetime

import tempdir
from tree_sitter_languages import get_language, get_parser

from bigbuild import RepoInstance
from bigbuild.inference.builder.prompt import (
    file_template,
    instruction,
    lazy_prompt,
    task_information_template,
)
from bigbuild.utils import load_bigbuild_dataset, progress
from bigbuild.utils.repo import get_repo, lang2suffix, show_project_structure

languages = ["python", "rust", "csharp", "javascript"]
tree_sitter_parsers = {
    "python": get_parser("python"),
    "rust": get_parser("rust"),
    "csharp": get_parser("c_sharp"),
    "javascript": get_parser("javascript"),
}

tree_sitter_languages = {
    "python": get_language("python"),
    "rust": get_language("rust"),
    "csharp": get_language("c_sharp"),
    "javascript": get_language("javascript"),
}

tree_sitter_queries = {
    "python": tree_sitter_languages["python"].query(
        "[(import_statement) (import_from_statement)] @import",
    ),
    "rust": tree_sitter_languages["rust"].query("(use_declaration) @use"),
    "csharp": tree_sitter_languages["csharp"].query("(using_directive) @use"),
    "javascript": tree_sitter_languages["javascript"].query(
        "(import_statement) @import"
    ),
}


def pattern_retrieve(src_section: str, content: str, ts_parser, query):
    dep_related_statements = []
    content: bytes = content.encode()
    tree = ts_parser.parse(content)
    for node, _ in query.captures(tree.root_node):
        dep_related_statements.append(content[node.start_byte : node.end_byte].decode())
    if len(dep_related_statements) == 0:
        return None
    ret = "..."
    for s in dep_related_statements:
        if s in src_section:
            continue
        ret += f"\n{s}"
        ret += "\n..."
    return ret


def all_src_files(root: pathlib.Path, lang_suffix: list[str]) -> list[str]:
    files_to_include = []
    for suffix in lang_suffix:
        for file in glob.glob(f"{root}/**/*{suffix}", recursive=True):
            file = str(pathlib.Path(file).relative_to(root))
            # exclude setup.py
            if file == "setup.py":
                continue
            files_to_include.append(file)
    return files_to_include


def make_prompt(
    instance: RepoInstance,
    repo_cache: pathlib.Path | None,
    pattern: bool = False,
) -> list[dict]:
    with tempdir.TempDir() as temp_dir:
        if not repo_cache:
            project_root = pathlib.Path(temp_dir) / instance.instance_id
            print(f"Downloading {instance.instance_id} to {project_root}")
            get_repo(instance, project_root)
            print(f"Downloaded {instance.instance_id}")
        else:
            project_root = repo_cache
            if not repo_cache.exists():
                print("Repo not found in cache, downloading...")
                get_repo(instance, repo_cache)
                print(f"Downloaded {instance.instance_id}")
        project_structure = show_project_structure(
            project_root, exclude_dirs=[".git", ".github"]
        )
        src_files = all_src_files(project_root, lang2suffix[instance.language.lower()])
        if pattern:
            ts_parser = tree_sitter_parsers[instance.language.lower()]
            ts_query = tree_sitter_queries[instance.language.lower()]
            src_section = ""
            for file in src_files:
                retrieved = pattern_retrieve(
                    src_section, (project_root / file).read_text(), ts_parser, ts_query
                )
                if not retrieved:
                    continue
                src_section += "\n" + file_template.format(path=file, content=retrieved)
        else:
            src_section = "\n".join(
                file_template.format(
                    path=file, content=(project_root / file).read_text()
                )
                for file in src_files
            )

        env_specs = "\n".join(f"- {k}: {v}" for k, v in instance.env_specs.items())
        build_section = "\n".join(
            file_template.format(path=file, content=(project_root / file).read_text())
            for file in instance.build_files
        )
        task = task_information_template.format(
            project_structure=project_structure,
            env_specs=env_specs,
            src_section=src_section,
            build_section=build_section,
        )
        prompt = instruction + "\n" + task + "\n" + instruction + "\n" + lazy_prompt
        return [
            {
                "role": "system",
                "content": f"You are a senior expert in {instance.language.lower()}",
            },
            {"role": "user", "content": prompt},
        ]


def main(
    result_path: str = f"results/prompt-{datetime.now().isoformat()}.jsonl",
    dataset_name_or_path: str = "data/regular.jsonl",
    repo_cache: str | None = None,
    pattern: bool = False,
):
    dataset = load_bigbuild_dataset(dataset_name_or_path)
    results = []
    with progress("Making prompts") as p:
        for instance in p.track(dataset):
            project_root = (
                pathlib.Path(repo_cache)
                / instance.language.lower()
                / instance.instance_id
                if repo_cache
                else None
            )
            prompts = make_prompt(instance, project_root, pattern)
            results.append(
                dict(
                    instance_id=instance.instance_id,
                    language=instance.language.lower(),
                    prompts=prompts,
                )
            )
        with open(result_path, "w") as f:
            for result in results:
                f.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
