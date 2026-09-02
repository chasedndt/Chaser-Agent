"""Explicit memory lifecycle transitions."""

from __future__ import annotations

from dataclasses import replace

from chaser_agent.memory.models import MemoryRecord, MemoryStatus

VALID_TRANSITIONS: dict[MemoryStatus, frozenset[MemoryStatus]] = {
    "raw": frozenset({"candidate"}),
    "candidate": frozenset({"reviewed", "rejected"}),
    "reviewed": frozenset({"promoted", "rejected"}),
    "promoted": frozenset({"stale", "disputed", "archived"}),
    "stale": frozenset({"reviewed", "disputed", "archived"}),
    "disputed": frozenset({"reviewed", "archived", "rejected"}),
    "archived": frozenset(),
    "rejected": frozenset(),
}


def can_transition(current: MemoryStatus, target: MemoryStatus) -> bool:
    return target in VALID_TRANSITIONS[current]


def transition_memory(
    memory: MemoryRecord,
    target: MemoryStatus,
    *,
    reviewed_at: str | None = None,
    reviewer_id: str | None = None,
    promoted_at: str | None = None,
) -> MemoryRecord:
    if not can_transition(memory.status, target):
        raise ValueError(f"invalid memory transition: {memory.status} -> {target}")
    if target == "reviewed":
        if not reviewed_at or not reviewer_id:
            raise ValueError("reviewed transition requires reviewed_at and reviewer_id")
        return replace(memory, status=target, reviewed_at=reviewed_at, reviewer_id=reviewer_id)
    if target == "promoted":
        if not promoted_at or not reviewer_id:
            raise ValueError("promoted transition requires promoted_at and approving reviewer_id")
        return replace(memory, status=target, promoted_at=promoted_at, reviewer_id=reviewer_id)
    return replace(memory, status=target)
