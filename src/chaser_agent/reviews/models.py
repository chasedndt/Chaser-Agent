"""Human-review record model."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Literal


ReviewDecision = Literal["pass", "needs_revision", "fail"]


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    run_id: str
    reviewer_id: str
    reviewed_at: str
    source_fidelity_score: int
    inference_separation_score: int
    uncertainty_handling_score: int
    action_usefulness_score: int
    memory_safety_score: int
    decision: ReviewDecision
    reviewer_notes: str
    corrected_claims: tuple[str, ...] = ()
    corrected_inferences: tuple[str, ...] = ()
    accepted_action_ids: tuple[str, ...] = ()
    rejected_action_ids: tuple[str, ...] = ()
    accepted_memory_ids: tuple[str, ...] = ()
    rejected_memory_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "source_fidelity_score",
            "inference_separation_score",
            "uncertainty_handling_score",
            "action_usefulness_score",
            "memory_safety_score",
        ):
            score = getattr(self, field_name)
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 3:
                raise ValueError(f"{field_name} must be an integer from 0 through 3")
        if self.decision not in {"pass", "needs_revision", "fail"}:
            raise ValueError("decision must be pass, needs_revision, or fail")
        for accepted_name, rejected_name in (
            ("accepted_action_ids", "rejected_action_ids"),
            ("accepted_memory_ids", "rejected_memory_ids"),
        ):
            overlap = set(getattr(self, accepted_name)) & set(getattr(self, rejected_name))
            if overlap:
                raise ValueError(f"IDs cannot be both accepted and rejected: {', '.join(sorted(overlap))}")

    @property
    def total_score(self) -> int:
        return sum(
            (
                self.source_fidelity_score,
                self.inference_separation_score,
                self.uncertainty_handling_score,
                self.action_usefulness_score,
                self.memory_safety_score,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def record_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReviewRecord":
        tuple_fields = {
            "corrected_claims",
            "corrected_inferences",
            "accepted_action_ids",
            "rejected_action_ids",
            "accepted_memory_ids",
            "rejected_memory_ids",
        }
        normalized = {key: tuple(item) if key in tuple_fields else item for key, item in value.items()}
        return cls(**normalized)
