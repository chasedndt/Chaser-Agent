"""Explicit profile for AI-engineering and research sources."""

from __future__ import annotations

from typing import Any

from chaser_agent.workflows.base import SafeReviewProfile


class AIEngineeringResearchReviewProfile(SafeReviewProfile):
    def build_uncertainties(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        uncertainties = super().build_uncertainties(claim_ids, source_text)
        uncertainties.append(
            {
                "uncertainty_id": "uncertainty-003",
                "label": "research_limitations_not_verified",
                "explanation": "Methodology, baselines, evaluation coverage, citations, and production transfer have not been independently verified.",
                "related_claim_ids": claim_ids,
            }
        )
        return uncertainties

    def build_inferences(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "inference_id": "inference-001",
                "inference_text": "Reported research results may motivate an evaluation or architecture question, but they are not production truth.",
                "based_on_claim_ids": claim_ids,
                "confidence": "medium",
                "uncertainty_label_ids": ["uncertainty-001", "uncertainty-003"],
            }
        ]

    def build_actions(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "action-001",
                "action_text": "Review the methodology, baselines, evaluation limits, and implementation assumptions.",
                "source_claim_ids": claim_ids,
                "rationale": "Research claims need evidence and transfer checks before implementation decisions.",
                "risk_level": "low",
                "requires_approval": True,
                "blocked_reason": None,
                "suggested_owner": "human_operator",
            },
            {
                "action_id": "action-002",
                "action_text": "Consider creating a bounded evaluation or RFC candidate after human review.",
                "source_claim_ids": claim_ids,
                "rationale": "A reviewable candidate preserves separation between research and adopted architecture.",
                "risk_level": "low",
                "requires_approval": True,
                "blocked_reason": None,
                "suggested_owner": "human_operator",
            },
        ]


PROFILE = AIEngineeringResearchReviewProfile(
    profile_id="ai_engineering_research_review",
    display_name="AI engineering research review",
    version="0.1.0",
    purpose="Review AI-engineering research while preserving methodology, evaluation, and provenance limits.",
    allowed_input_types=("note", "text", "markdown", "paper_notes", "other_safe_text"),
    claim_hints=("reported results", "methodology", "baselines", "evaluation", "implementation questions"),
    uncertainty_rules=("do not treat paper claims as production truth", "identify missing baselines and eval limits"),
    action_policy=("propose evaluation or RFC candidates", "require human approval"),
    memory_policy=("do not convert research claims directly into durable project truth",),
    tags=("ai-engineering", "research", "source-review"),
)
