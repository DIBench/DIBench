import json
import shutil
from pathlib import Path
from typing import List

from termcolor import colored

from bigbuild.harness.evaluator import BuildEvaluator
from bigbuild.harness.utils import CacheLevel, EvalArgs
from bigbuild.utils import cprint, load_bigbuild_dataset, progress


def main(
    result_dir: str,
    text_eval: bool = True,
    exec_eval: bool = True,
    patch_eval: bool = False,
    remove_fake_eval: bool = False,
    dataset_name_or_path: str = "data/regular.jsonl",
    repo_cache: str = ".cache/repo-regular",
    cache_level: CacheLevel = "all",
    timeout: int = 1200,
    resume: bool = True,
    id_range: List[int] = None,
) -> None:
    dataset = load_bigbuild_dataset(dataset_name_or_path)
    if id_range is not None:
        dataset = dataset[id_range[0] : id_range[1]]
    result_dir: Path = Path(result_dir)
    with progress("Evaluating") as p:
        for instance in p.track(dataset):
            print(
                colored(
                    f"Evaluating {instance.language}/{instance.instance_id}", "green"
                )
            )
            instance_id = instance.instance_id
            prediction_path: Path = (
                result_dir / instance.language.lower() / instance_id / "patch.diff"
            )
            if prediction_path.exists():
                prediction = prediction_path.read_text()
            else:
                cprint("Prediction file not found, skipping evaluation", "yellow")
                continue
            eval_result_path = (
                result_dir
                / instance.language.lower()
                / instance_id
                / "eval-result.json"
            )
            project_root = (
                Path(repo_cache) / instance.language.lower() / instance.instance_id
            )
            workspace = (
                result_dir / instance.language.lower() / instance_id / "eval-workspace"
            )
            if not resume:
                # remove workspace and eval result if exists
                if workspace.exists():
                    shutil.rmtree(workspace)
                if eval_result_path.exists():
                    eval_result_path.unlink()
            args = EvalArgs(
                instance=instance,
                project_root=project_root,
                prediction=prediction,
                workspace=workspace,
                text_eval=text_eval,
                exec_eval=exec_eval,
                patch_eval=patch_eval,
                remove_fake_eval=remove_fake_eval,
                cache_level=cache_level,
                timeout=timeout,
                resume=resume,
            )
            evaluator = BuildEvaluator(args)
            evaluator.run()
            with open(eval_result_path, "w") as f:
                json.dump(evaluator.result, f, indent=2)


if __name__ == "__main__":
    from fire import Fire

    Fire(main)
