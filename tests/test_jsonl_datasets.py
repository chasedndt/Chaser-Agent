from pathlib import Path
from scripts.validate_jsonl import validate_jsonl

def test_golden_jsonl_files_are_valid_and_seeded():
    files=sorted(Path("evals/datasets/golden").glob("*.jsonl"))
    assert len(files) >= 6
    for path in files:
        assert validate_jsonl(path) >= 3
