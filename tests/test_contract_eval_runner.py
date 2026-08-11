import json
from pathlib import Path

import chaser_agent.evals.contract_runner as contract_runner
from chaser_agent.evals.contract_runner import read_contract_jsonl, run_contract_case, run_contract_jsonl_eval


DATASET = Path("evals/datasets/contract/layer0_contract_seed.jsonl")


def test_contract_seed_has_one_pending_review_case_per_initial_family():
    rows = read_contract_jsonl(DATASET)

    assert len(rows) == 6
    assert {row["layer0_clause"] for row in rows} == {
        "no_auto_promotion",
        "injection_resistance",
        "claim_evidence_integrity",
        "uncertainty_honesty",
        "action_boundary",
        "authority_stamps",
    }
    assert all(row["human_review_required"] is True for row in rows)
    assert all(row["provenance"]["review_status"] == "pending_operator_review" for row in rows)


def test_contract_seed_executes_real_artifact_assertions(tmp_path: Path):
    output = tmp_path / "contract-results.jsonl"

    results = run_contract_jsonl_eval(DATASET, output, repo_root=Path.cwd())

    assert len(results) == 6
    assert all(result.passed for result in results)
    assert all(result.score == 1.0 for result in results)
    assert all(result.assertion_details for result in results)
    written = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(written) == 6
    assert all(row["layer0_clause"] for row in written)
    assert all(row["assertion_details"] for row in written)


def test_contract_failure_names_clause_assertion_and_observed_value(monkeypatch):
    row = read_contract_jsonl(DATASET)[0]
    real_builder = contract_runner.build_source_card_artifacts

    def build_corrupted_artifacts(*args, **kwargs):
        artifacts = real_builder(*args, **kwargs)
        artifacts["source_card.json"]["promotion_status"] = "approved_elsewhere"
        return artifacts

    monkeypatch.setattr(contract_runner, "build_source_card_artifacts", build_corrupted_artifacts)

    result = run_contract_case(row, repo_root=Path.cwd())

    assert result.passed is False
    assert result.layer0_clause == "no_auto_promotion"
    assert "promotion_status" in result.notes
    assert "approved_elsewhere" in result.notes
    assert any(detail["passed"] is False for detail in result.assertion_details)


def test_injected_source_text_cannot_forge_authority_fields():
    row = next(row for row in read_contract_jsonl(DATASET) if row["layer0_clause"] == "injection_resistance")

    result = run_contract_case(row, repo_root=Path.cwd())

    assert result.passed is True
    assert result.output["assertions_passed"] == result.output["assertions_total"]
