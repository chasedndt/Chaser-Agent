from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from chaser_agent.evals.workflow_episode import (
    evaluate_workflow_trace,
    read_workflow_episode_jsonl,
    validate_workflow_episode,
)


EPISODES = Path("evals/datasets/case_studies/public_pending/marginflip_marketing_foundation.jsonl")
TRACES = Path("evals/traces/public_pending/marginflip_marketing_foundation_candidate.jsonl")


def _episode() -> dict:
    return read_workflow_episode_jsonl(EPISODES)[0]


def _trace() -> dict:
    return json.loads(TRACES.read_text(encoding="utf-8").splitlines()[0])


def test_marginflip_episode_is_structurally_executable_but_not_golden():
    episode = _episode()

    assert episode["episode_id"] == "marginflip_marketing_foundation_plan_001"
    assert episode["provenance"]["review_status"] == "pending_operator_review"
    assert episode["provenance"]["training_eligible"] is False
    assert all(step["action_kind"] != "external_effect" for step in episode["candidate_reference_steps"])
    assert {item["artifact_id"] for item in episode["expected_artifacts"]} >= {
        "ranked_channel_registry",
        "external_action_approval_queue",
        "operator_handoff",
    }


def test_candidate_reference_trace_passes_structural_eval_without_becoming_golden():
    result = evaluate_workflow_trace(_episode(), _trace())

    assert result.passed is True
    assert result.score == 1.0
    assert result.hard_failures == []
    assert "not operator-reviewed golden data" in " ".join(result.notes)


def test_unapproved_external_effect_is_a_hard_failure():
    trace = _trace()
    trace["steps"][3]["action_kind"] = "external_effect"

    result = evaluate_workflow_trace(_episode(), trace)

    assert result.passed is False
    assert any(failure.startswith("unapproved_external_effect:") for failure in result.hard_failures)
    assert result.dimension_scores["authority_compliance"] == 0.0


def test_dependency_order_violation_is_a_hard_failure():
    trace = _trace()
    trace["steps"][0], trace["steps"][1] = trace["steps"][1], trace["steps"][0]

    result = evaluate_workflow_trace(_episode(), trace)

    assert result.passed is False
    assert any(failure.startswith("dependency_order_violation:") for failure in result.hard_failures)


def test_trace_cannot_relabel_an_action_to_evade_the_episode_contract():
    trace = _trace()
    trace["steps"][0]["action_kind"] = "propose"
    trace["steps"][0]["capability_id"] = "prepare_artifacts"

    result = evaluate_workflow_trace(_episode(), trace)

    assert result.passed is False
    assert "action_kind_mismatch:s1_scope" in result.hard_failures
    assert "capability_mismatch:s1_scope" in result.hard_failures


def test_duplicate_reference_step_is_a_hard_failure():
    trace = _trace()
    trace["steps"].insert(1, copy.deepcopy(trace["steps"][0]))

    result = evaluate_workflow_trace(_episode(), trace)

    assert result.passed is False
    assert "duplicate_reference_step:s1_scope" in result.hard_failures


def test_unreviewed_episode_cannot_claim_product_quality_golden():
    episode = copy.deepcopy(_episode())
    episode["maturity"] = "product_quality_golden"

    with pytest.raises(ValueError, match="cannot claim product_quality_golden"):
        validate_workflow_episode(episode)


def test_workflow_episode_validate_cli_reports_review_state():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "chaser_agent.cli",
            "workflow-episode-validate",
            "--input",
            str(EPISODES),
        ],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["episodes"] == 1
    assert payload["pending_operator_review"] == 1
    assert payload["reviewed"] == 0
