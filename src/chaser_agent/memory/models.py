"""Standalone memory records and lifecycle vocabulary."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MemoryStatus = Literal["raw", "candidate", "reviewed", "promoted", "stale", "disputed", "archived", "rejected"]
MEMORY_STATUSES: tuple[MemoryStatus, ...] = (
    "raw", "candidate", "reviewed", "promoted", "stale", "disputed", "archived", "rejected"
)


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    status: MemoryStatus
    scope: str
    privacy_class: str
    stability: str
    confidence: str
    source_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    run_id: str
    created_at: str
    reviewed_at: str | None = None
    reviewer_id: str | None = None
    promoted_at: str | None = None
    supersedes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    metadata_json: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in MEMORY_STATUSES:
            raise ValueError(f"invalid memory status: {self.status}")
        if not self.memory_id or not self.content or not self.run_id:
            raise ValueError("memory_id, content, and run_id are required")
        if self.status in {"reviewed", "promoted"} and (not self.reviewed_at or not self.reviewer_id):
            raise ValueError(f"{self.status} memory requires reviewed_at and reviewer_id")
        if self.status == "promoted" and not self.promoted_at:
            raise ValueError("promoted memory requires promoted_at")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def record_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MemoryRecord":
        normalized = dict(value)
        for field_name in ("source_refs", "claim_refs", "supersedes", "tags"):
            normalized[field_name] = tuple(normalized.get(field_name, ()))
        return cls(**normalized)


@dataclass(frozen=True)
class MemoryFeedback:
    feedback_id: str
    memory_id: str
    reviewer_id: str
    feedback: Literal["useful", "irrelevant", "stale", "disputed"]
    created_at: str
    notes: str = ""
