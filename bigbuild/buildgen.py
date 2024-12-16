import json
import os
import pathlib
from typing import Literal

from bigbuild.utils import progress
from bigbuild.utils.llm.provider import LLMProvider, make_provider


def buildgen(
    target_dir: pathlib.Path,
    model: LLMProvider,
    dataset: list[dict],
    resume: bool = True,
    max_new_tokens: int = 8_000,
):
    backend_type: str = type(model).__name__
    with progress(backend_type) as p:
        for instance in p.track(dataset):
            instance_id: str = instance["instance_id"]
            lang: str = instance["language"]
            raw_f_name = target_dir / lang / instance_id / "raw_response.md"
            if resume and raw_f_name.exists():
                p.console.print("Skipping", instance_id)
                continue

            p.console.print("Building", instance_id)
            os.makedirs(target_dir / lang / instance_id, exist_ok=True)
            raw_response = model.generate_reply(
                n=1,
                system_msg=instance["prompts"][0]["content"],
                message=instance["prompts"][1]["content"],
                max_tokens=max_new_tokens,
            )[0]
            with open(target_dir / lang / instance_id / "raw_response.md", "w") as f:
                f.write(raw_response)
            p.console.print("Building", instance_id, "Done!")


def main(
    prompt_path: str = "results/bigbuild-prompts.jsonl",
    target_dir: str = "results",
    model_name: str = "gpt-4o-20240806",
    backend: Literal["azure", "openai"] = "openai",
    max_new_tokens: int = 8_000,
    resume: bool = True,
    # for openai
    base_url: str | None = None,
    # concurrency
    id_range: list[int] | None = None,
):
    model = make_provider(model_name, backend, base_url)

    model_name_abbr = model_name
    if model_name.count("/") > 2:
        model_name_abbr = model_name.split("/")[-3].replace("--", "/")
        if model_name_abbr.startswith("models/"):
            model_name_abbr = model_name_abbr[7:]
            model_name_abbr = model_name_abbr.replace("/", "--")
        print(f"Using model name abbreviation: {model_name_abbr}")
    target_dir = pathlib.Path(target_dir) / model_name_abbr


    with open(prompt_path, "r") as f:
        raw_dataset: list[dict] = [json.loads(line) for line in f]

    dataset = []
    for instance in raw_dataset:
        instance_id: str = instance["instance_id"]
        lang: str = instance["language"]
        raw_f_name = target_dir / lang / instance_id / "raw_response.md"
        if resume and raw_f_name.exists():
            continue
        dataset.append(instance)
    print(f'==== Total instances to be inferred: {len(dataset)} ====')


    if id_range is not None:
        print("Using id range:", id_range)
        dataset = dataset[id_range[0] : id_range[1]]
    buildgen(
        target_dir=target_dir,
        model=model,
        dataset=dataset,
        max_new_tokens=max_new_tokens,
        resume=resume,
    )


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
