from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


NON_VISUAL_EVIDENCE_TYPES = {"file_check", "content_check", "dom_check", "log_check", "api_check"}
VISUAL_EVIDENCE_TYPES = {"screenshot", "visual_state", "screen_recording"}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_visual_eval_run_id(input_path: Path, created_at: str) -> str:
    digest = hashlib.sha256(f"{input_path.as_posix()}:{created_at}".encode("utf-8")).hexdigest()[:10]
    return f"visual-completion-eval-{created_at.replace(':', '').replace('-', '')}-{digest}"


def _evidence_items(case: dict[str, Any]) -> list[dict[str, Any]]:
    raw = case.get("evidence", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _label(item: dict[str, Any], index: int) -> str:
    value = item.get("label") or item.get("id") or f"evidence_{index}"
    return str(value)


def evaluate_visual_completion(case: dict[str, Any]) -> dict[str, Any]:
    """Classify a visual/computer-use completion case with closed authority.

    This is a deterministic, provider-free evaluator seed. It does not inspect real
    pixels yet; it evaluates already-collected evidence metadata so ChaseOS can
    build smoke/eval contracts before live browser/computer-use authority exists.
    """

    evidence = _evidence_items(case)
    evidence_used = [_label(item, index) for index, item in enumerate(evidence)]
    evidence_types = {str(item.get("type", "unknown")) for item in evidence}
    supported = [item for item in evidence if item.get("supports_expected_outcome") is True]
    failures = [item for item in evidence if item.get("indicates_failure") is True]
    has_visual = bool(evidence_types & VISUAL_EVIDENCE_TYPES)
    has_non_visual = bool(evidence_types & NON_VISUAL_EVIDENCE_TYPES)

    authority = {
        "can_mark_complete": False,
        "requires_operator_review": True,
        "mode": "advisory_review_only",
    }

    if failures:
        return {
            "case_id": str(case.get("case_id", "unknown")),
            "outcome": "failed",
            "confidence": 0.9,
            "evidence_used": evidence_used,
            "missing_evidence": [],
            "recommended_action": "fix_or_escalate",
            "rationale": "Evidence explicitly indicates task failure; do not mark complete.",
            "authority": authority,
        }

    missing_evidence: list[str] = []
    if not evidence:
        missing_evidence.append("completion_evidence")
    if has_visual and not has_non_visual:
        missing_evidence.append("non_visual_confirmation")
    if not has_visual:
        missing_evidence.append("visual_confirmation")

    if has_visual and has_non_visual and len(supported) >= 2:
        return {
            "case_id": str(case.get("case_id", "unknown")),
            "outcome": "verified_success_advisory",
            "confidence": 0.88,
            "evidence_used": evidence_used,
            "missing_evidence": [],
            "recommended_action": "operator_review_before_completion",
            "rationale": "Visual and non-visual evidence support the expected outcome, but advisory evaluation cannot consume approval or mark completion.",
            "authority": authority,
        }

    rationale = "Evidence is insufficient to prove the desired outcome."
    if has_visual and not has_non_visual:
        rationale = "Screenshot-only evidence cannot prove desired outcome; non-visual confirmation is required."

    return {
        "case_id": str(case.get("case_id", "unknown")),
        "outcome": "attempted_unverified",
        "confidence": 0.42 if evidence else 0.1,
        "evidence_used": evidence_used,
        "missing_evidence": missing_evidence,
        "recommended_action": "collect_more_evidence_or_human_review",
        "rationale": rationale,
        "authority": authority,
    }


def load_visual_eval_cases(input_path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parsed = json.loads(stripped)
        if not isinstance(parsed, dict):
            raise ValueError(f"line {line_number} is not a JSON object")
        cases.append(parsed)
    return cases


def build_visual_eval_run(input_path: Path, out_root: Path, created_at: str | None = None) -> Path:
    created_at = created_at or utc_now_iso()
    run_id = make_visual_eval_run_id(input_path, created_at)
    run_folder = out_root / run_id
    run_folder.mkdir(parents=True, exist_ok=False)

    cases = load_visual_eval_cases(input_path)
    results = [evaluate_visual_completion(case) for case in cases]
    results_path = run_folder / "visual_completion_results.jsonl"
    results_path.write_text(
        "\n".join(json.dumps(result, sort_keys=True) for result in results) + ("\n" if results else ""),
        encoding="utf-8",
    )

    run_log = {
        "run_id": run_id,
        "created_at": created_at,
        "input_path": input_path.as_posix(),
        "results_path": results_path.as_posix(),
        "case_count": len(cases),
        "outcome_counts": _outcome_counts(results),
        "authority": {
            "provider_calls": "none",
            "browser_or_computer_use": "none",
            "fine_tuning": "none",
            "canonical_mutation": "none",
            "approval_consumption": "none",
            "mode": "deterministic_local_smoke_eval",
        },
    }
    (run_folder / "run_log.json").write_text(json.dumps(run_log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_folder


def _outcome_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        outcome = str(result.get("outcome", "unknown"))
        counts[outcome] = counts.get(outcome, 0) + 1
    return counts
