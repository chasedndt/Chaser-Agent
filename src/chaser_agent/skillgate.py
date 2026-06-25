from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chaser_agent.run_artifacts import current_repo_commit, write_json

SLOW_BEGIN = "<!-- CHASER:SLOW-STATE:BEGIN -->"
SLOW_END = "<!-- CHASER:SLOW-STATE:END -->"
MAX_EDIT_BUDGET = 8


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_skill_gate_run_id(baseline_path: Path, created_at: str) -> str:
    digest = hashlib.sha256(f"{baseline_path.as_posix()}:{created_at}".encode("utf-8")).hexdigest()[:10]
    safe_stem = baseline_path.stem.replace(".", "-").replace("_", "-").lower()[:48]
    stamp = created_at.replace("-", "").replace(":", "").replace("Z", "z")
    return f"skill-gate-{stamp}-{safe_stem}-{digest}"


def read_metrics(metrics_path: Path) -> dict[str, Any]:
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    for field in ("baseline_score", "candidate_score", "held_out_split_id", "edit_count", "verifier"):
        if field not in data:
            raise ValueError(f"metrics missing required field: {field}")
    return data


def extract_slow_state(text: str) -> str | None:
    begin = text.find(SLOW_BEGIN)
    end = text.find(SLOW_END)
    if begin == -1 and end == -1:
        return None
    if begin == -1 or end == -1 or end < begin:
        return "__MALFORMED_SLOW_STATE__"
    return text[begin : end + len(SLOW_END)]


def protected_section_preserved(baseline_text: str, candidate_text: str) -> bool:
    return extract_slow_state(baseline_text) == extract_slow_state(candidate_text)


def count_tokens_rough(text: str) -> int:
    return len([part for part in text.replace("\n", " ").split(" ") if part.strip()])


def build_skill_gate_artifacts(
    *,
    baseline_path: Path,
    candidate_path: Path,
    metrics_path: Path,
    run_id: str,
    created_at: str,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline_text = baseline_path.read_text(encoding="utf-8")
    candidate_text = candidate_path.read_text(encoding="utf-8")
    metrics = read_metrics(metrics_path)

    baseline_score = float(metrics["baseline_score"])
    candidate_score = float(metrics["candidate_score"])
    score_delta = round(candidate_score - baseline_score, 10)
    strict_improvement_passed = candidate_score > baseline_score
    slow_state_ok = protected_section_preserved(baseline_text, candidate_text)
    edit_count = int(metrics["edit_count"])
    bounded_edit_budget_passed = 1 <= edit_count <= MAX_EDIT_BUDGET

    rejection_reasons: list[str] = []
    if not strict_improvement_passed:
        rejection_reasons.append("Candidate score must strictly improve held-out validation score.")
    if not slow_state_ok:
        rejection_reasons.append("Protected slow-state section changed.")
    if not bounded_edit_budget_passed:
        rejection_reasons.append(f"Edit count must be between 1 and {MAX_EDIT_BUDGET}.")

    decision = "candidate_patch_reviewable" if not rejection_reasons else "candidate_patch_rejected"
    baseline_hash = hashlib.sha256(baseline_text.encode("utf-8")).hexdigest()
    candidate_hash = hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()

    packet: dict[str, Any] = {
        "run_id": run_id,
        "created_at": created_at,
        "source_paper": "SkillOpt: Executive Strategy for Self-Evolving Agent Skills (arXiv:2605.23904)",
        "decision": decision,
        "acceptance_policy": "strict_held_out_improvement_only",
        "baseline_skill_path": baseline_path.as_posix(),
        "candidate_skill_path": candidate_path.as_posix(),
        "metrics_path": metrics_path.as_posix(),
        "baseline_sha256": baseline_hash,
        "candidate_sha256": candidate_hash,
        "baseline_score": baseline_score,
        "candidate_score": candidate_score,
        "score_delta": score_delta,
        "held_out_split_id": metrics["held_out_split_id"],
        "verifier": metrics["verifier"],
        "strict_improvement_passed": strict_improvement_passed,
        "protected_section_preserved": slow_state_ok,
        "bounded_edit_budget_passed": bounded_edit_budget_passed,
        "edit_count": edit_count,
        "max_edit_budget": MAX_EDIT_BUDGET,
        "baseline_token_estimate": count_tokens_rough(baseline_text),
        "candidate_token_estimate": count_tokens_rough(candidate_text),
        "rejection_reasons": rejection_reasons,
        "review_status": "pending_operator_review",
        "write_performed": False,
        "autonomous_skill_mutation": False,
        "provider_calls": "none",
        "external_api_calls": "none",
        "runtime_adapters": "none",
        "browser_or_computer_use": "none",
        "canonical_promotion": "none",
    }
    review: dict[str, Any] = {
        "run_id": run_id,
        "review_type": "skill_patch_candidate",
        "summary": "Review-only SkillOpt-style gate for a candidate skill patch. The baseline skill is not modified.",
        "operator_questions": [
            "Does the held-out verifier measure the behavior this skill is meant to improve?",
            "Is the candidate patch compact and understandable enough to merge?",
            "Does the candidate preserve slow-state governance lessons?",
        ],
        "recommended_next_step": "Apply the candidate patch only after human review if the verifier and diff are trusted.",
        "blocked_actions": [
            "No autonomous skill mutation was performed.",
            "No provider, API, runtime adapter, browser, MCP, or fine-tuning call was performed.",
            "No ChaseOS canonical truth or memory promotion was performed.",
        ],
        "packet_ref": "skill_gate_packet.json",
    }
    run_log = {
        "run_id": run_id,
        "created_at": created_at,
        "command_family": "skill-gate",
        "repo_commit": current_repo_commit(repo_root),
        "outputs": ["skill_gate_packet.json", "skill_patch_review.json", "run_log.json"],
        "provider_calls": "none",
        "external_api_calls": "none",
        "runtime_adapters": "none",
        "mcp_activation": "none",
        "browser_or_computer_use": "none",
        "fine_tuning_or_training": "none",
        "write_performed": False,
        "autonomous_skill_mutation": False,
        "review_required": True,
        "notes": "Deterministic local SkillGate run. Review-only patch proposal gate inspired by SkillOpt.",
    }
    return {"skill_gate_packet.json": packet, "skill_patch_review.json": review}, run_log


def write_skill_gate_run(run_folder: Path, artifacts: dict[str, Any], run_log: dict[str, Any]) -> None:
    run_folder.mkdir(parents=True, exist_ok=False)
    for filename, payload in artifacts.items():
        write_json(run_folder / filename, payload)
    write_json(run_folder / "run_log.json", run_log)



def build_agent_skills_sentinel_preflight(*, package_path: Path, sentinel_report_path: Path) -> dict[str, Any]:
    """Build a Chaser Agent preflight decision from a ChaseOS Agent Skills Sentinel report.

    The preflight consumes an existing report artifact only. It does not execute
    the package, activate a runtime adapter, call providers, consume approvals,
    or promote the package. Even a safe Sentinel verdict is held for an explicit
    operator/Gate allowlist decision.
    """
    package = package_path.resolve()
    report_file = sentinel_report_path.resolve()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    if report.get("surface_id") != "chaseos_agent_skills_sentinel":
        raise ValueError("sentinel_report_path is not an Agent Skills Sentinel report")
    verdict = str(report.get("verdict") or "caution")
    if verdict == "do_not_install":
        decision = "activation_blocked"
        required_next_step = "remediate_and_rescan_before_gate_review"
    elif verdict == "caution":
        decision = "operator_gate_review_required"
        required_next_step = "operator_gate_risk_review"
    else:
        decision = "awaiting_allowlist_promotion"
        required_next_step = "operator_gate_allowlist_decision"
    artifact = report.get("artifact") or {}
    report_artifact = report.get("report_artifact") or {}
    return {
        "surface_id": "chaser_agent_agent_skills_sentinel_preflight",
        "package_path": package.as_posix(),
        "report_path": report_file.as_posix(),
        "sentinel_verdict": verdict,
        "sentinel_risk_score": report.get("risk_score"),
        "decision": decision,
        "activation_allowed": False,
        "required_next_step": required_next_step,
        "artifact_sha256": artifact.get("sha256"),
        "report_sha256": report_artifact.get("report_sha256"),
        "authority": {
            "package_execution_performed": False,
            "activation_performed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "approval_consumed": False,
            "canonical_mutation_performed": False,
        },
    }
