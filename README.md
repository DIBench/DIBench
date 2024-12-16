### Evaluating LLM-based Code Intelligence on Dependency Inference in Repository Scope

Ensure that Docker engine is installed and running on your machine.

> [!Important]
>
>
> Our testing infrastructure requires [⚙️sysbox](https://github.com/nestybox/sysbox) (a Docker runtime) to be installed on your system to ensure isolation and security.

```shell
# Suggested Python version: 3.10
poetry install .
```

## Dataset
regular.jsonl and large.jsonl are dataset file for regular sets and large sets


## Unzip Repository Instances
```
unzip repo-large.zip
unzip repo-regular.zip
```

## Run All-In-On

### prepare prompts
```shell
python -m bigbuild.make_prompts \
     --result_path prompts-regular.jsonl \
     --dataset_name_or_path regular.jsonl \
     --repo_cache repo-regular
```

### Generate
```shell
python -m bigbuild.buildgen \
    --prompt_path prompts-regular.jsonl \
    --target_dir results\all-in-one \ # results will be saved in results\all-in-one\[model]
    --model [model] \
    --backend "openai" \
    # --base_url [base_url] \ # if you using vllm service
```

## Run Imports-Only
### prepare prompts
```shell
poetry run python -m bigbuild.make_prompts \
     --result_path [prompts-regular-imports.jsonl|prompts-large-imports.jsonl]
     --dataset [regular.jsonl|large.jsonl] \
     --pattern \
```
### Generate
```shell
python -m bigbuild.buildgen \
    --prompt_path bigbuild-prompts-regular.jsonl\
    --target_dir results\all-in-one \
    --model_name [model] \
    --backend "openai"
```

## Run File-Iterate
```shell
python -m bigbuild.inference.run_builder \
    --model {model} \
    --backend  "openai" \
    # --base_url [base_url] # if you using vllm server
    --dataset_name_or_path [regular.jsonl|large.jsonl] \
    --repo_cache [repo-regular/|repo-large/]
```

## Evaluation

```shell
python -m bigbuild.eval \
    --result_dir results\[all-in-one|imports|file-iter]\{model} \ # the root of results generated by three baseline, json format results evaluating is WIP
    --repo_cache [repo-regular|repo-large] \
    --dataset_name_or_path [regular|large].jsonl
```


## Run Experiments with VLLM

### start server
```shell
pip install vllm
vllm serve [model] --port [port] --trust-remote-code
```

