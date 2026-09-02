"""Review-run validation and record creation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from chaser_agent.reviews.models import ReviewDecision, ReviewRecord


REQUIRED_RUN_ARTIFACTS = (
    "source_card.json",
    "claims_table.json",
    "evidence_snippets.json",
    "uncertainty_labels.json",
    "action_candidates.json",
    "memory_candidates.json",
    "human_review_packet.json",
    "run_log.json",
)


def artifact_hashes(run_folder: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((run_folder / name).read_bytes()).hexdigest()
        for name in REQUIRED_RUN_ARTIFACTS
        if (run_folder / name).is_file()
    }


def load_review_material(run_folder: str | Path) -> dict[str, Any]:
    folder = Path(run_folder)
    missing = [name for name in REQUIRED_RUN_ARTIFACTS if not (folder / name).is_file()]
    if missing:
        raise ValueError(f"run folder is missing required artifacts: {', '.join(missing)}")
    return {name: json.loads((folder / name).read_text(encoding="utf-8")) for name in REQUIRED_RUN_ARTIFACTS}


def _validate_selection(selected: tuple[str, ...], available: set[str], label: str) -> None:
    unknown = sorted(set(selected) - available)
    if unknown:
        raise ValueError(f"unknown {label}: {', '.join(unknown)}")


def create_review_record(
    run_folder: str | Path,
    *,
    reviewer_id: str,
    scores: tuple[int, int, int, int, int],
    decision: ReviewDecision,
    reviewer_notes: str,
    corrected_claims: tuple[str, ...] = (),
    corrected_inferences: tuple[str, ...] = (),
    accepted_action_ids: tuple[str, ...] = (),
    rejected_action_ids: tuple[str, ...] = (),
    accepted_memory_ids: tuple[str, ...] = (),
    rejected_memory_ids: tuple[str, ...] = (),
    reviewed_at: str | None = None,
) -> ReviewRecord:
    material = load_review_material(run_folder)
    source_card = material["source_card.json"]
    run_id = str(source_card["run_id"])
    action_ids = {row["action_id"] for row in material["action_candidates.json"]["action_candidates"]}
    memory_ids = {row["memory_candidate_id"] for row in material["memory_candidates.json"]["memory_candidates"]}
    _validate_selection(accepted_action_ids + rejected_action_ids, action_ids, "action candidate ID")
    _validate_selection(accepted_memory_ids + rejected_memory_ids, memory_ids, "memory candidate ID")

    timestamp = reviewed_at or datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    seed = json.dumps(
        {
            "run_id": run_id,
            "reviewer_id": reviewer_id,
            "reviewed_at": timestamp,
            "decision": decision,
            "scores": scores,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    review_id = "review-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return ReviewRecord(
        review_id=review_id,
        run_id=run_id,
        reviewer_id=reviewer_id,
        reviewed_at=timestamp,
        source_fidelity_score=scores[0],
        inference_separation_score=scores[1],
        uncertainty_handling_score=scores[2],
        action_usefulness_score=scores[3],
        memory_safety_score=scores[4],
        decision=decision,
        reviewer_notes=reviewer_notes,
        corrected_claims=corrected_claims,
        corrected_inferences=corrected_inferences,
        accepted_action_ids=accepted_action_ids,
        rejected_action_ids=rejected_action_ids,
        accepted_memory_ids=accepted_memory_ids,
        rejected_memory_ids=rejected_memory_ids,
    )
