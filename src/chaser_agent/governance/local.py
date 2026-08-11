"""Human-authorized local governance with no external execution authority."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ReviewPolicyProposal:
    minimum_total: int = 12
    minimum_dimension: int = 2
    block_critical_safety_failure: bool = True
    enforced: bool = False


class LocalGovernance:
    """P0.1 governance: review and promotion are human decisions; action execution is disabled."""

    def __init__(self, operator_id: str, review_policy: ReviewPolicyProposal | None = None) -> None:
        if not operator_id.strip():
            raise ValueError("operator_id is required")
        self.operator_id = operator_id
        self.review_policy = review_policy or ReviewPolicyProposal()

    def can_candidate_be_reviewed(self, candidate: Mapping[str, Any]) -> bool:
        return bool(candidate) and candidate.get("promotion_status", "candidate_only") == "candidate_only"

    def can_memory_be_promoted(self, memory: Any, review: Any) -> bool:
        return (
            getattr(memory, "status", None) == "reviewed"
            and getattr(review, "reviewer_id", None) == self.operator_id
            and getattr(review, "decision", None) == "pass"
            and getattr(memory, "memory_id", None) in set(getattr(review, "accepted_memory_ids", ()))
        )

    def can_action_be_executed(self, action: Mapping[str, Any]) -> bool:
        return False

    def approver_for(self, operation: str) -> str:
        return self.operator_id

    def policy_for(self, operation: str) -> Mapping[str, Any]:
        return {
            "operation": operation,
            "authority": "human_operator",
            "external_action_execution": "disabled",
            "review_policy_proposal": asdict(self.review_policy),
        }

    def audit_decision(self, operation: str, approved: bool, reasons: Iterable[str]) -> Mapping[str, Any]:
        created_at = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        payload = {
            "operation": operation,
            "approved": approved,
            "approved_by": self.operator_id if approved else None,
            "reasons": list(reasons),
            "created_at": created_at,
            "policy": dict(self.policy_for(operation)),
        }
        payload["audit_id"] = "audit-" + hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:20]
        return payload
