"""Explicit website-design review profile."""

from __future__ import annotations

from typing import Any

from chaser_agent.workflows.base import SafeReviewProfile, memory_from_claim


class WebsiteDesignReviewProfile(SafeReviewProfile):
    def build_uncertainties(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        uncertainties = super().build_uncertainties(claim_ids, source_text)
        uncertainties.append(
            {
                "uncertainty_id": "uncertainty-003",
                "label": "visual_context_required",
                "explanation": "Hierarchy, contrast, spacing, readability, restraint, and user intent require screenshots or other visual proof for confident review.",
                "related_claim_ids": claim_ids,
            }
        )
        return uncertainties

    def build_inferences(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "inference_id": "inference-001",
                "inference_text": "A website review should check hierarchy, contrast, spacing, readability, restraint, user intent, and the available visual evidence.",
                "based_on_claim_ids": claim_ids,
                "confidence": "medium",
                "uncertainty_label_ids": ["uncertainty-001", "uncertainty-003"],
            }
        ]

    def build_actions(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "action-001",
                "action_text": "Inspect screenshots or other visual proof before recommending website-design changes.",
                "source_claim_ids": claim_ids,
                "rationale": "Text-only evidence is insufficient for a confident visual assessment.",
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
        for claim in claims:
            if claim["claim_type"] in {"requirement", "decision", "constraint"}:
                return [memory_from_claim(claim, privacy_class, scope="workflow", stability="unknown")]
        return []


PROFILE = WebsiteDesignReviewProfile(
    profile_id="website_design_review",
    display_name="Website design review",
    version="0.1.0",
    purpose="Review website-design evidence with explicit visual-context requirements.",
    allowed_input_types=("note", "text", "markdown", "other_safe_text"),
    claim_hints=("hierarchy", "contrast", "spacing", "readability", "restraint", "user intent"),
    uncertainty_rules=("request screenshots or visual proof when needed", "do not infer appearance from text alone"),
    action_policy=("propose evidence review", "avoid over-decoration", "require human approval"),
    memory_policy=("only propose source-grounded durable design constraints",),
    tags=("website", "design", "visual-review"),
)
