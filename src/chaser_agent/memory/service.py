"""Connect explicit human reviews to governed memory records."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from chaser_agent.core.protocols import GovernanceBackend
from chaser_agent.memory.models import MemoryRecord
from chaser_agent.memory.sqlite_store import SQLiteMemoryStore
from chaser_agent.reviews.models import ReviewRecord
from chaser_agent.reviews.service import load_review_material


def reviewed_memories_from_review(
    store: SQLiteMemoryStore,
    run_folder: str | Path,
    review: ReviewRecord,
) -> list[MemoryRecord]:
    material = load_review_material(run_folder)
    source_card = material["source_card.json"]
    claims_by_id = {row["claim_id"]: row for row in material["claims_table.json"]["claims"]}
    evidence_by_id = {row["snippet_id"]: row for row in material["evidence_snippets.json"]["evidence_snippets"]}
    candidates = {row["memory_candidate_id"]: row for row in material["memory_candidates.json"]["memory_candidates"]}
    selected = [(candidate_id, "reviewed") for candidate_id in review.accepted_memory_ids]
    selected += [(candidate_id, "rejected") for candidate_id in review.rejected_memory_ids]
    results: list[MemoryRecord] = []
    for candidate_id, target in selected:
        candidate = candidates[candidate_id]
        evidence = evidence_by_id.get(candidate["evidence_snippet_id"], {})
        claim_refs = tuple(evidence.get("supports_claim_ids", ()))
        seed = f"{review.review_id}\0{candidate_id}\0{candidate['candidate_text']}\0{candidate['scope']}"
        memory_id = "mem-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        record = MemoryRecord(
            memory_id=memory_id,
            memory_type="semantic",
            content=candidate["candidate_text"],
            status="candidate",
            scope=candidate["scope"],
            privacy_class=candidate["privacy_class"],
            stability=candidate["stability"],
            confidence="unreviewed",
            source_refs=(source_card["source_id"],),
            claim_refs=claim_refs,
            run_id=review.run_id,
            created_at=source_card["created_at"],
            tags=(source_card.get("workflow_profile", "general_source_review"),),
            metadata_json={
                "candidate_id": candidate_id,
                "review_id": review.review_id,
                "evidence_snippet_id": candidate["evidence_snippet_id"],
                "claim_texts": [claims_by_id[item]["claim_text"] for item in claim_refs if item in claims_by_id],
            },
        )
        store.create(record)
        results.append(
            store.transition(
                memory_id,
                target,
                reviewed_at=review.reviewed_at,
                reviewer_id=review.reviewer_id,
            )
        )
    return results


def promote_memory(
    store: SQLiteMemoryStore,
    memory_id: str,
    review: ReviewRecord,
    governance: GovernanceBackend,
) -> MemoryRecord:
    memory = store.get(memory_id)
    if memory is None:
        raise ValueError(f"memory not found: {memory_id}")
    if not governance.can_memory_be_promoted(memory, review):
        raise PermissionError("governance denied memory promotion")
    audit = dict(governance.audit_decision("memory.promote", True, ["reviewed and accepted by human operator"]))
    promoted_at = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    return store.transition(
        memory_id,
        "promoted",
        promoted_at=promoted_at,
        reviewer_id=review.reviewer_id,
        audit_record=audit,
    )
