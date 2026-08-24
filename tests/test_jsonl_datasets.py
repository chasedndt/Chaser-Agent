from pathlib import Path
from scripts.validate_jsonl import expand_inputs, validate_jsonl

def test_golden_jsonl_files_are_valid_and_seeded():
    files=sorted(Path("evals/datasets/golden").glob("*.jsonl"))
    assert len(files) >= 6
    for path in files:
        assert validate_jsonl(path) >= 3


def test_jsonl_validator_expands_shell_globs_on_windows(tmp_path):
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_text('{"id":"a"}\n', encoding="utf-8")
    second.write_text('{"id":"b"}\n', encoding="utf-8")

    assert expand_inputs([str(tmp_path / "*.jsonl")]) == [first, second]
