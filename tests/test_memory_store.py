from __future__ import annotations

from pathlib import Path

import pytest

from chaser_agent.governance.local import LocalGovernance
from chaser_agent.memory.models import MemoryRecord
from chaser_agent.memory.service import promote_memory
from chaser_agent.memory.sqlite_store import SQLiteMemoryStore
from chaser_agent.reviews.models import ReviewRecord


def _memory(**overrides) -> MemoryRecord:
    values = {
        "memory_id": "mem-1",
        "memory_type": "semantic",
        "content": "The local review policy requires human approval.",
        "status": "candidate",
        "scope": "workflow",
        "privacy_class": "public_toy",
        "stability": "likely_stable",
        "confidence": "unreviewed",
        "source_refs": ("source-1",),
        "claim_refs": ("claim-1",),
        "run_id": "run-1",
        "created_at": "2026-08-11T12:00:00Z",
        "tags": ("governance", "review"),
        "metadata_json": {"candidate_id": "memory-001"},
    }
    values.update(overrides)
    return MemoryRecord(**values)


def _review(**overrides) -> ReviewRecord:
    values = {
        "review_id": "review-1",
        "run_id": "run-1",
        "reviewer_id": "operator-1",
        "reviewed_at": "2026-08-11T12:10:00Z",
        "source_fidelity_score": 3,
        "inference_separation_score": 3,
        "uncertainty_handling_score": 3,
        "action_usefulness_score": 3,
        "memory_safety_score": 3,
        "decision": "pass",
        "reviewer_notes": "Accepted.",
        "accepted_memory_ids": ("memory-001",),
    }
    values.update(overrides)
    return ReviewRecord(**values)


def test_memory_history_is_append_only_and_invalid_transitions_fail(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.create(_memory())

    with pytest.raises(ValueError, match="invalid memory transition"):
        store.transition("mem-1", "stale")
    reviewed = store.transition(
        "mem-1", "reviewed", reviewed_at="2026-08-11T12:10:00Z", reviewer_id="operator-1"
    )

    assert reviewed.status == "reviewed"
    assert [item.status for item in store.history("mem-1")] == ["candidate", "reviewed"]


def test_promotion_requires_governance_and_creates_audited_durable_state(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.create(_memory())
    store.transition("mem-1", "reviewed", reviewed_at="2026-08-11T12:10:00Z", reviewer_id="operator-1")

    with pytest.raises(ValueError, match="governance audit"):
        store.transition(
            "mem-1", "promoted", promoted_at="2026-08-11T12:20:00Z", reviewer_id="operator-1"
        )

    promoted = promote_memory(store, "mem-1", _review(), LocalGovernance("operator-1"))

    assert promoted.status == "promoted"
    assert promoted.promoted_at
    assert [item.status for item in store.history("mem-1")] == ["candidate", "reviewed", "promoted"]


def test_retrieval_filters_promoted_memory_without_embeddings(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.create(_memory())
    store.transition("mem-1", "reviewed", reviewed_at="2026-08-11T12:10:00Z", reviewer_id="operator-1")

    assert store.retrieve("human approval", scope="workflow", tags=("governance",)) == []
    promoted = promote_memory(store, "mem-1", _review(), LocalGovernance("operator-1"))

    assert store.retrieve("human approval", scope="workflow", tags=("governance",)) == [promoted]
    assert store.retrieve("unrelated") == []
    assert store.retrieve(statuses=("reviewed",)) == []


def test_memory_feedback_is_persisted_without_silent_state_change(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    store.create(_memory())

    feedback = store.add_feedback("mem-1", "operator-1", "stale", "Needs re-checking.")

    assert store.list_feedback("mem-1") == [feedback]
    assert store.get("mem-1").status == "candidate"
