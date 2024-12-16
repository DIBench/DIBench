from bigbuild.utils import load_bigbuild_dataset


def test_load_buildmark_dataset():
    load_bigbuild_dataset("data/regular.jsonl")
    load_bigbuild_dataset("data/regular.jsonl")
