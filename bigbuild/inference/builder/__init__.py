from pathlib import Path

from .base import Builder, Repo

__all__ = [
    "make_builder",
    "Builder",
    "Repo",
]


def make_builder(
    builder_type: str,
    repo: Repo,
    result_dir: Path,
    model_name: str = "gpt-4o-20240806",
    backend: str = "azure",
    resume: bool = True,
    max_seq_len: int = 1024 * 100,
    max_new_tokens: int = 1024 * 8,
    base_url: str | None = None,
):
    assert result_dir.exists(), f"cache dir {result_dir} for builder not exists"
    if builder_type == "file-iter":
        from .file_iter.builder import FileIterBuilder

        return FileIterBuilder(
            repo=repo,
            model_name=model_name,
            backend=backend,
            result_dir=result_dir,
            resume=resume,
            max_seq_len=max_seq_len,
            max_new_tokens=max_new_tokens,
            base_url=base_url,
        )
    elif builder_type == "pattern":
        from .pattern.builder import PatternBuilder

        return PatternBuilder(
            repo=repo,
            model_name=model_name,
            backend=backend,
            result_dir=result_dir,
            resume=resume,
            max_seq_len=max_seq_len,
            max_new_tokens=max_new_tokens,
            base_url=base_url,
        )
    else:
        raise ValueError(f"Unknown builder type {builder_type}")
