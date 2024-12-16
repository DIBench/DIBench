from pathlib import Path
from typing import Literal

from bigbuild.inference.builder import Repo, make_builder
from bigbuild.utils import cprint, load_bigbuild_dataset, progress


def build(
    repo: Repo,
    result_dir: Path,
    builder_type: Literal["file-iter", "pattern"] = "file-iter",
    model: str = "gpt-4o-20240806",
    backend: str = "azure",
    resume: bool = True,
    max_seq_len: int = 1000 * 120,
    max_new_tokens: int = 1000 * 8,
    base_url: str | None = None,
):
    try:
        builder = make_builder(
            builder_type=builder_type,
            repo=repo,
            result_dir=result_dir,
            model_name=model,
            backend=backend,
            resume=resume,
            max_seq_len=max_seq_len,
            max_new_tokens=max_new_tokens,
            base_url=base_url,
        )
        builder.patchgen()
        cprint(f"Finished building {repo.name}", "green")
    except Exception as e:
        import traceback

        traceback.print_exc()
        cprint(f"Failed to build {repo.name}: {e}", "red")


def main(
    result_dir: str = "results/",
    builder_type: Literal["file-iter", "pattern"] = "file-iter",
    dataset_name_or_path: str = "data/regular.jsonl-Mini",
    repo_cache: str = ".cache/repo-mini/",
    resume: bool = True,
    model: str = "gpt-4o-20240806",
    backend: str = "azure",
    max_seq_len: int = 1000 * 120,
    max_new_tokens: int = 1000 * 8,
    base_url: str | None = None,
    id_range: list[int] = [0, 400],
):
    repo_cache = Path(repo_cache)
    result_dir: Path = Path(result_dir)
    if "Mini" in dataset_name_or_path:
        result_dir = result_dir / builder_type / model
    else:
        result_dir = result_dir / f"{builder_type}-large" / model
    dataset = load_bigbuild_dataset(dataset_name_or_path)
    if not result_dir.exists():
        result_dir.mkdir(parents=True, exist_ok=True)
    start, end = id_range
    with progress("Building") as p:
        for instance in p.track(dataset[start:end]):
            project_root = repo_cache / instance.language.lower() / instance.instance_id
            repo = Repo(
                name=instance.instance_id,
                root=project_root,
                language=instance.language.lower(),
                build_files=tuple(instance.build_files),
                env_specs=instance.env_specs,
            )
            cur_result_dir = (
                result_dir / instance.language.lower() / instance.instance_id
            )
            cur_result_dir.mkdir(parents=True, exist_ok=True)
            try:
                builder = make_builder(
                    builder_type=builder_type,
                    repo=repo,
                    result_dir=cur_result_dir,
                    model_name=model,
                    backend=backend,
                    resume=resume,
                    max_seq_len=max_seq_len,
                    max_new_tokens=max_new_tokens,
                    base_url=base_url,
                )
                builder.patchgen()
                cprint(f"Finished building {repo.name}", "green")
            except Exception as e:
                import traceback

                traceback.print_exc()
                cprint(f"Failed to build {repo.name}: {e}", "red")


if __name__ == "__main__":
    import fire

    fire.Fire(main)
