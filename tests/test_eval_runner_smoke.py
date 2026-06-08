from chaser_agent.evals.runner import run_jsonl_eval

def test_eval_runner_smoke(tmp_path):
    output=tmp_path / "results.jsonl"
    results=run_jsonl_eval("evals/datasets/golden/source_card_summary_eval.jsonl", output)
    assert len(results) == 3
    assert output.exists()
    assert all(result.task == "source_card_summary" for result in results)
