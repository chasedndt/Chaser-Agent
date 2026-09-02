"""Safe defaults shared by built-in workflow profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REVIEW_DIMENSIONS = (
    "source_fidelity",
    "inference_separation",
    "uncertainty_handling",
    "action_usefulness",
    "memory_safety",
)

FORBIDDEN_EXTERNAL_ACTIONS = (
    "public_post",
    "message",
    "payment",
    "trade",
    "deployment",
    "account_change",
    "credential_operation",
    "destructive_file_change",
    "external_tool_call",
)


@dataclass(frozen=True)
class SafeReviewProfile:
    profile_id: str
    display_name: str
    version: str
    purpose: str
    allowed_input_types: tuple[str, ...]
    claim_hints: tuple[str, ...]
    uncertainty_rules: tuple[str, ...]
    action_policy: tuple[str, ...]
    memory_policy: tuple[str, ...]
    forbidden_actions: tuple[str, ...] = FORBIDDEN_EXTERNAL_ACTIONS
    required_review_dimensions: tuple[str, ...] = REVIEW_DIMENSIONS
    tags: tuple[str, ...] = ()

    def build_uncertainties(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "uncertainty_id": "uncertainty-001",
                "label": "requires_review",
                "explanation": "Deterministic extraction does not establish that the source statements are correct; human review is required.",
                "related_claim_ids": claim_ids,
            },
            {
                "uncertainty_id": "uncertainty-002",
                "label": "promotion_blocked",
                "explanation": "Review artifacts and memory candidates are not approved durable memory until an explicit governed promotion.",
                "related_claim_ids": claim_ids,
            },
        ]

    def build_inferences(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "inference_id": "inference-001",
                "inference_text": "The extracted claims should be checked against their source evidence before they influence a decision.",
                "based_on_claim_ids": claim_ids,
                "confidence": "medium",
                "uncertainty_label_ids": ["uncertainty-001"],
            }
        ]

    def build_actions(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "action-001",
                "action_text": "Review the extracted claims, evidence, inferences, and uncertainties.",
                "source_claim_ids": claim_ids,
                "rationale": "The local deterministic pass produces review candidates, not completed actions.",
                "risk_level": "low",
                "requires_approval": True,
                "blocked_reason": None,
                "suggested_owner": "human_operator",
            }
        ]

    def build_memories(
        self,
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        privacy_class: str,
    ) -> list[dict[str, Any]]:
        return []


def memory_from_claim(
    claim: dict[str, Any],
    privacy_class: str,
    index: int = 1,
    *,
    scope: str = "source",
    stability: str = "unknown",
) -> dict[str, Any]:
    return {
        "memory_candidate_id": f"memory-{index:03d}",
        "candidate_text": claim["claim_text"],
        "evidence_snippet_id": claim["evidence_snippet_id"],
        "scope": scope,
        "stability": stability,
        "privacy_class": privacy_class,
        "promotion_status": "candidate_only",
        "review_required": True,
        "rejection_reason": None,
    }
