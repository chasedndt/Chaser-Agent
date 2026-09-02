import json
from collections import Counter
from pathlib import Path

import chaser_agent.evals.contract_runner as contract_runner
from chaser_agent.evals.contract_runner import read_contract_jsonl, run_contract_case, run_contract_jsonl_eval


DATASET = Path("evals/datasets/contract/layer0_contract_seed.jsonl")


LAYER0_FAMILIES = {
    "no_auto_promotion",
    "injection_resistance",
    "claim_evidence_integrity",
    "uncertainty_honesty",
    "action_boundary",
    "authority_stamps",
}

# The design doc's coverage bar: a family with 1-2 cases is a seed, not coverage.
MINIMUM_CASES_PER_FAMILY = 5


def test_contract_seed_meets_the_coverage_bar_for_every_family():
    """Assert the coverage property, not a frozen case count.

    An earlier version asserted `len(rows) == 6`, which turned the seed size into
    an invariant and failed the moment coverage improved. The bar that matters is
    per-family depth.
    """
    rows = read_contract_jsonl(DATASET)
    counts = Counter(row["layer0_clause"] for row in rows)

    assert set(counts) == LAYER0_FAMILIES
    thin = {family: count for family, count in counts.items() if count < MINIMUM_CASES_PER_FAMILY}
    assert not thin, f"families below the coverage bar of {MINIMUM_CASES_PER_FAMILY}: {thin}"


def test_contract_seed_cases_are_all_unreviewed_and_uniquely_identified():
    rows = read_contract_jsonl(DATASET)
    identifiers = [row["id"] for row in rows]

    assert len(identifiers) == len(set(identifiers)), "contract case ids must be unique"
    assert all(row["human_review_required"] is True for row in rows)
    assert all(row["provenance"]["review_status"] == "pending_operator_review" for row in rows), (
        "coverage is not operator-reviewed golden data; every case stays pending until reviewed"
    )


def test_contract_seed_executes_real_artifact_assertions(tmp_path: Path):
    output = tmp_path / "contract-results.jsonl"

    results = run_contract_jsonl_eval(DATASET, output, repo_root=Path.cwd())

    expected_case_count = len(read_contract_jsonl(DATASET))
    assert len(results) == expected_case_count
    assert all(result.passed for result in results)
    assert all(result.score == 1.0 for result in results)
    assert all(result.assertion_details for result in results)
    # Every case must carry real executable assertions, not pass vacuously.
    assert all(result.output["assertions_total"] >= 1 for result in results)
    written = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(written) == expected_case_count
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
