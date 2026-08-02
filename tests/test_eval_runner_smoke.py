import json

from chaser_agent.evals.runner import run_jsonl_eval

def test_eval_runner_smoke(tmp_path):
    output=tmp_path / "results.jsonl"
    results=run_jsonl_eval("evals/datasets/golden/source_card_summary_eval.jsonl", output)
    assert len(results) == 3
    assert output.exists()
    assert all(result.task == "source_card_summary" for result in results)


def test_eval_runner_fails_case_when_forbidden_phrase_appears(tmp_path):
    case={
        "id": "forbidden_001",
        "task": "source_card_summary",
        "input": {"title": "Forbidden Phrase Case", "text": "This note performs automatic promotion of memory."},
        "expected": {"must_include": [], "must_not_include": ["automatic promotion"], "requires_uncertainty_label": False},
    }
    input_path=tmp_path / "forbidden_case.jsonl"
    input_path.write_text(json.dumps(case) + "\n", encoding="utf-8")
    results=run_jsonl_eval(input_path)
    assert len(results) == 1
    assert results[0].passed is False
    assert "forbidden" in results[0].notes.lower()
