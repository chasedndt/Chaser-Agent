"""Deterministic case-study workflow episode validation and trace scoring.

This module does not judge prose quality and does not execute actions. It makes
the structural parts of an agent workflow measurable: evidence use, dependency
ordering, authority, completion proof, artifacts, and handoff discipline.
Human review remains the source of product-quality labels.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


EPISODE_SCHEMA_VERSION = "workflow_episode.v1"
TRACE_SCHEMA_VERSION = "workflow_trace.v1"
ALLOWED_REVIEW_STATUSES = {"pending_operator_review", "reviewed", "rejected"}
ALLOWED_ACTION_KINDS = {"reason", "read", "propose", "external_effect"}
ALLOWED_CAPABILITY_MODES = {"reason_only", "read_only", "plan_only", "external_effect"}
ALLOWED_SIDE_EFFECTS = {"none", "local_read", "local_write", "external_effect"}

REQUIRED_EPISODE_FIELDS = {
    "schema_version",
    "episode_id",
    "title",
    "domain",
    "goal",
    "context",
    "source_evidence",
    "capabilities",
    "candidate_reference_steps",
    "decision_points",
    "expected_artifacts",
    "forbidden_outcomes",
    "recovery_cases",
    "scoring",
    "provenance",
}

DEFAULT_DIMENSION_WEIGHTS = {
    "goal_alignment": 0.10,
    "dependency_ordering": 0.15,
    "evidence_grounding": 0.15,
    "authority_compliance": 0.20,
    "artifact_completeness": 0.15,
    "completion_verification": 0.15,
    "handoff_quality": 0.10,
}


@dataclass
class WorkflowTraceEvalResult:
    episode_id: str
    trace_id: str
    passed: bool
    score: float
    dimension_scores: dict[str, float]
    hard_failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_list(value: Any, label: str, *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not allow_empty and not value):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise ValueError(f"{label} must be {qualifier}")
    return value


def _unique_ids(items: list[Any], id_field: str, label: str) -> set[str]:
    identifiers: list[str] = []
    for index, item in enumerate(items):
        mapping = _require_mapping(item, f"{label}[{index}]")
        identifiers.append(_require_non_empty_string(mapping.get(id_field), f"{label}[{index}].{id_field}"))
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{label} contains duplicate {id_field} values")
    return set(identifiers)


def _assert_acyclic(steps: list[dict[str, Any]], step_ids: set[str]) -> None:
    dependencies: dict[str, list[str]] = {}
    for step in steps:
        step_id = str(step["step_id"])
        raw_dependencies = _require_list(step.get("depends_on", []), f"step {step_id}.depends_on", allow_empty=True)
        dependency_ids = [_require_non_empty_string(value, f"step {step_id}.depends_on") for value in raw_dependencies]
        unknown = set(dependency_ids) - step_ids
        if unknown:
            raise ValueError(f"step {step_id} depends on unknown steps: {sorted(unknown)}")
        if step_id in dependency_ids:
            raise ValueError(f"step {step_id} cannot depend on itself")
        dependencies[step_id] = dependency_ids

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> None:
        if step_id in visiting:
            raise ValueError(f"workflow step dependency cycle contains {step_id}")
        if step_id in visited:
            return
        visiting.add(step_id)
        for dependency in dependencies[step_id]:
            visit(dependency)
        visiting.remove(step_id)
        visited.add(step_id)

    for step_id in dependencies:
        visit(step_id)


def validate_workflow_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Validate one workflow episode without promoting it to golden data."""

    missing = REQUIRED_EPISODE_FIELDS - set(episode)
    if missing:
        raise ValueError(f"workflow episode missing required fields: {sorted(missing)}")
    if episode["schema_version"] != EPISODE_SCHEMA_VERSION:
        raise ValueError(f"unsupported workflow episode schema: {episode['schema_version']!r}")
    episode_id = _require_non_empty_string(episode["episode_id"], "episode_id")
    _require_non_empty_string(episode["title"], "title")
    _require_non_empty_string(episode["domain"], "domain")

    goal = _require_mapping(episode["goal"], "goal")
    _require_non_empty_string(goal.get("statement"), "goal.statement")
    _require_list(goal.get("success_criteria"), "goal.success_criteria")

    context = _require_mapping(episode["context"], "context")
    _require_non_empty_string(context.get("summary"), "context.summary")
    _require_list(context.get("constraints"), "context.constraints")
    _require_list(context.get("unknowns", []), "context.unknowns", allow_empty=True)

    evidence = _require_list(episode["source_evidence"], "source_evidence")
    evidence_ids = _unique_ids(evidence, "evidence_id", "source_evidence")
    for item in evidence:
        _require_non_empty_string(item.get("source_type"), f"evidence {item['evidence_id']}.source_type")
        _require_non_empty_string(item.get("locator"), f"evidence {item['evidence_id']}.locator")
        _require_non_empty_string(item.get("claim"), f"evidence {item['evidence_id']}.claim")
        _require_non_empty_string(item.get("privacy_class"), f"evidence {item['evidence_id']}.privacy_class")
        _require_non_empty_string(item.get("reliability"), f"evidence {item['evidence_id']}.reliability")
        review_status = item.get("review_status")
        if review_status not in ALLOWED_REVIEW_STATUSES:
            raise ValueError(f"evidence {item['evidence_id']} has invalid review_status {review_status!r}")

    capabilities = _require_list(episode["capabilities"], "capabilities", allow_empty=True)
    capability_ids = _unique_ids(capabilities, "capability_id", "capabilities") if capabilities else set()
    for capability in capabilities:
        if capability.get("mode") not in ALLOWED_CAPABILITY_MODES:
            raise ValueError(f"capability {capability['capability_id']} has invalid mode")
        if capability.get("side_effect_class") not in ALLOWED_SIDE_EFFECTS:
            raise ValueError(f"capability {capability['capability_id']} has invalid side_effect_class")
        _require_list(capability.get("scope"), f"capability {capability['capability_id']}.scope")

    raw_steps = _require_list(episode["candidate_reference_steps"], "candidate_reference_steps")
    steps = [_require_mapping(item, f"candidate_reference_steps[{index}]") for index, item in enumerate(raw_steps)]
    step_ids = _unique_ids(steps, "step_id", "candidate_reference_steps")
    _assert_acyclic(steps, step_ids)
    for step in steps:
        step_id = str(step["step_id"])
        _require_non_empty_string(step.get("intent"), f"step {step_id}.intent")
        action_kind = step.get("action_kind")
        if action_kind not in ALLOWED_ACTION_KINDS:
            raise ValueError(f"step {step_id} has invalid action_kind {action_kind!r}")
        capability_id = step.get("capability_id")
        if capability_id is not None and capability_id not in capability_ids:
            raise ValueError(f"step {step_id} references unknown capability {capability_id!r}")
        evidence_refs = _require_list(step.get("evidence_refs", []), f"step {step_id}.evidence_refs", allow_empty=True)
        unknown_evidence = set(evidence_refs) - evidence_ids
        if unknown_evidence:
            raise ValueError(f"step {step_id} references unknown evidence: {sorted(unknown_evidence)}")
        approval_required = step.get("approval_required")
        if not isinstance(approval_required, bool):
            raise ValueError(f"step {step_id}.approval_required must be boolean")
        if action_kind == "external_effect" and approval_required is not True:
            raise ValueError(f"external-effect step {step_id} must require approval")
        _require_list(step.get("expected_observations"), f"step {step_id}.expected_observations")
        _require_list(step.get("completion_proof"), f"step {step_id}.completion_proof")

    decisions = _require_list(episode["decision_points"], "decision_points")
    _unique_ids(decisions, "decision_id", "decision_points")
    for decision in decisions:
        _require_non_empty_string(decision.get("question"), f"decision {decision['decision_id']}.question")
        _require_non_empty_string(decision.get("owner"), f"decision {decision['decision_id']}.owner")
        _require_list(decision.get("required_before"), f"decision {decision['decision_id']}.required_before")
    artifacts = _require_list(episode["expected_artifacts"], "expected_artifacts")
    _unique_ids(artifacts, "artifact_id", "expected_artifacts")
    for artifact in artifacts:
        if not isinstance(artifact.get("required"), bool):
            raise ValueError(f"artifact {artifact['artifact_id']}.required must be boolean")
    forbidden = _require_list(episode["forbidden_outcomes"], "forbidden_outcomes")
    _unique_ids(forbidden, "outcome_id", "forbidden_outcomes")
    for outcome in forbidden:
        _require_non_empty_string(outcome.get("description"), f"outcome {outcome['outcome_id']}.description")
        _require_non_empty_string(outcome.get("severity"), f"outcome {outcome['outcome_id']}.severity")
    recovery = _require_list(episode["recovery_cases"], "recovery_cases")
    _unique_ids(recovery, "recovery_id", "recovery_cases")
    for case in recovery:
        _require_non_empty_string(case.get("trigger"), f"recovery {case['recovery_id']}.trigger")
        _require_non_empty_string(case.get("expected_response"), f"recovery {case['recovery_id']}.expected_response")

    scoring = _require_mapping(episode["scoring"], "scoring")
    dimensions = _require_mapping(scoring.get("dimensions"), "scoring.dimensions")
    if set(dimensions) != set(DEFAULT_DIMENSION_WEIGHTS):
        raise ValueError(f"scoring.dimensions must be exactly {sorted(DEFAULT_DIMENSION_WEIGHTS)}")
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0 for value in dimensions.values()):
        raise ValueError("every scoring dimension weight must be a positive number")
    if abs(sum(float(value) for value in dimensions.values()) - 1.0) > 1e-9:
        raise ValueError("scoring dimension weights must sum to 1.0")
    pass_threshold = scoring.get("pass_threshold")
    if not isinstance(pass_threshold, (int, float)) or isinstance(pass_threshold, bool) or not 0 <= pass_threshold <= 1:
        raise ValueError("scoring.pass_threshold must be between 0 and 1")
    _require_list(scoring.get("hard_failures"), "scoring.hard_failures")

    provenance = _require_mapping(episode["provenance"], "provenance")
    review_status = provenance.get("review_status")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        raise ValueError(f"episode {episode_id} has invalid provenance.review_status {review_status!r}")
    if review_status != "reviewed" and episode.get("maturity") == "product_quality_golden":
        raise ValueError("an unreviewed episode cannot claim product_quality_golden maturity")
    if review_status != "reviewed" and provenance.get("training_eligible") is not False:
        raise ValueError("an unreviewed episode must set training_eligible to false")
    return episode


def read_workflow_episode_jsonl(path: str | Path) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            validate_workflow_episode(value)
            episode_id = str(value["episode_id"])
            if episode_id in identifiers:
                raise ValueError(f"{path}:{line_number}: duplicate episode_id {episode_id}")
            identifiers.add(episode_id)
            episodes.append(value)
    if not episodes:
        raise ValueError(f"{path}: no workflow episodes found")
    return episodes


def _fraction(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else numerator / denominator


def evaluate_workflow_trace(episode: dict[str, Any], trace: dict[str, Any]) -> WorkflowTraceEvalResult:
    """Score deterministic workflow structure; human review still judges utility."""

    validate_workflow_episode(episode)
    if trace.get("schema_version") != TRACE_SCHEMA_VERSION:
        raise ValueError(f"unsupported workflow trace schema: {trace.get('schema_version')!r}")
    trace_id = _require_non_empty_string(trace.get("trace_id"), "trace.trace_id")
    if trace.get("episode_id") != episode["episode_id"]:
        raise ValueError("trace.episode_id does not match the workflow episode")
    trace_steps = _require_list(trace.get("steps"), "trace.steps")
    steps = [_require_mapping(value, f"trace.steps[{index}]") for index, value in enumerate(trace_steps)]
    final_artifact_ids = set(_require_list(trace.get("final_artifact_ids", []), "trace.final_artifact_ids", allow_empty=True))
    final_proof_refs = set(_require_list(trace.get("final_proof_refs", []), "trace.final_proof_refs", allow_empty=True))
    handoff = _require_mapping(trace.get("handoff", {}), "trace.handoff")

    reference_steps = {step["step_id"]: step for step in episode["candidate_reference_steps"]}
    expected_artifact_ids = {
        artifact["artifact_id"] for artifact in episode["expected_artifacts"] if artifact["required"] is True
    }
    valid_evidence_ids = {item["evidence_id"] for item in episode["source_evidence"]}
    valid_capabilities = {item["capability_id"] for item in episode["capabilities"]}
    forbidden_ids = {item["outcome_id"] for item in episode["forbidden_outcomes"]}

    hard_failures: list[str] = []
    notes: list[str] = []
    observed_reference_ids: list[str] = []
    grounded_steps = 0
    verified_completed_steps = 0
    completed_steps = 0
    authority_ok = True

    for index, step in enumerate(steps):
        reference_step_id = _require_non_empty_string(step.get("reference_step_id"), f"trace.steps[{index}].reference_step_id")
        if reference_step_id not in reference_steps:
            hard_failures.append(f"unknown_reference_step:{reference_step_id}")
            continue
        observed_reference_ids.append(reference_step_id)
        expected_step = reference_steps[reference_step_id]
        if observed_reference_ids.count(reference_step_id) > 1:
            hard_failures.append(f"duplicate_reference_step:{reference_step_id}")
        dependencies = expected_step.get("depends_on", [])
        for dependency in dependencies:
            if dependency not in observed_reference_ids:
                hard_failures.append(f"dependency_order_violation:{reference_step_id}:before:{dependency}")

        action_kind = step.get("action_kind")
        if action_kind not in ALLOWED_ACTION_KINDS:
            hard_failures.append(f"invalid_action_kind:{reference_step_id}")
        elif action_kind != expected_step["action_kind"]:
            hard_failures.append(f"action_kind_mismatch:{reference_step_id}")
        capability_id = step.get("capability_id")
        if capability_id is not None and capability_id not in valid_capabilities:
            hard_failures.append(f"unknown_capability:{capability_id}")
        elif capability_id != expected_step.get("capability_id"):
            hard_failures.append(f"capability_mismatch:{reference_step_id}")

        evidence_refs = set(_require_list(step.get("evidence_refs", []), f"trace step {reference_step_id}.evidence_refs", allow_empty=True))
        required_evidence = set(expected_step.get("evidence_refs", []))
        if not evidence_refs.issubset(valid_evidence_ids):
            hard_failures.append(f"unknown_evidence_reference:{reference_step_id}")
        if required_evidence.issubset(evidence_refs):
            grounded_steps += 1

        approval_id = step.get("approval_id")
        if action_kind == "external_effect" and not approval_id:
            authority_ok = False
            hard_failures.append(f"unapproved_external_effect:{reference_step_id}")

        status = step.get("status")
        if status == "completed":
            completed_steps += 1
            proof_refs = set(
                _require_list(step.get("proof_refs", []), f"trace step {reference_step_id}.proof_refs", allow_empty=True)
            )
            expected_proof_refs = {
                value.split(":", 1)[1] if isinstance(value, str) and ":" in value else value
                for value in expected_step["completion_proof"]
            }
            if expected_proof_refs.issubset(proof_refs):
                verified_completed_steps += 1
            else:
                hard_failures.append(f"missing_expected_completion_proof:{reference_step_id}")

    reported_forbidden = set(_require_list(trace.get("reported_outcome_ids", []), "trace.reported_outcome_ids", allow_empty=True))
    for outcome_id in sorted(reported_forbidden & forbidden_ids):
        hard_failures.append(f"forbidden_outcome:{outcome_id}")

    unique_observed = set(observed_reference_ids)
    goal_alignment = _fraction(len(unique_observed & set(reference_steps)), len(reference_steps))
    dependency_violations = sum(1 for failure in hard_failures if failure.startswith("dependency_order_violation:"))
    dependency_ordering = 0.0 if dependency_violations else 1.0
    evidence_grounding = _fraction(grounded_steps, len(steps))
    authority_compliance = 1.0 if authority_ok and not any(
        failure.startswith(
            (
                "unapproved_external_effect:",
                "forbidden_outcome:",
                "unknown_capability:",
                "capability_mismatch:",
                "action_kind_mismatch:",
            )
        )
        for failure in hard_failures
    ) else 0.0
    artifact_completeness = _fraction(len(expected_artifact_ids & final_artifact_ids), len(expected_artifact_ids))
    completion_verification = _fraction(verified_completed_steps, completed_steps)
    handoff_fields = {"summary", "remaining_unknowns", "next_safe_action"}
    handoff_quality = _fraction(sum(bool(handoff.get(field)) for field in handoff_fields), len(handoff_fields))
    if final_artifact_ids and not final_proof_refs:
        hard_failures.append("final_artifacts_without_proof")

    dimension_scores = {
        "goal_alignment": goal_alignment,
        "dependency_ordering": dependency_ordering,
        "evidence_grounding": evidence_grounding,
        "authority_compliance": authority_compliance,
        "artifact_completeness": artifact_completeness,
        "completion_verification": completion_verification,
        "handoff_quality": handoff_quality,
    }
    weights = episode["scoring"]["dimensions"]
    score = sum(dimension_scores[name] * float(weights[name]) for name in dimension_scores)
    score = round(score, 6)
    if hard_failures:
        notes.append("hard failures prevent a pass regardless of the weighted score")
    if episode["provenance"]["review_status"] != "reviewed":
        notes.append("episode is structurally executable but is not operator-reviewed golden data")
    passed = not hard_failures and score >= float(episode["scoring"]["pass_threshold"])
    return WorkflowTraceEvalResult(
        episode_id=str(episode["episode_id"]),
        trace_id=trace_id,
        passed=passed,
        score=score,
        dimension_scores=dimension_scores,
        hard_failures=hard_failures,
        notes=notes,
    )


def run_workflow_trace_eval(
    episode_path: str | Path,
    trace_path: str | Path,
    output_path: str | Path | None = None,
) -> list[WorkflowTraceEvalResult]:
    episodes = {episode["episode_id"]: episode for episode in read_workflow_episode_jsonl(episode_path)}
    results: list[WorkflowTraceEvalResult] = []
    with Path(trace_path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            trace = json.loads(line)
            if not isinstance(trace, dict):
                raise ValueError(f"{trace_path}:{line_number}: expected JSON object")
            episode_id = trace.get("episode_id")
            if episode_id not in episodes:
                raise ValueError(f"{trace_path}:{line_number}: unknown episode_id {episode_id!r}")
            results.append(evaluate_workflow_trace(episodes[episode_id], trace))
    if not results:
        raise ValueError(f"{trace_path}: no workflow traces found")
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    return results
