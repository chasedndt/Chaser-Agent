"""Default source-neutral review profile."""

from __future__ import annotations

from typing import Any

from chaser_agent.workflows.base import SafeReviewProfile, memory_from_claim


class GeneralSourceReviewProfile(SafeReviewProfile):
    def build_memories(
        self,
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        privacy_class: str,
    ) -> list[dict[str, Any]]:
        durable_markers = ("always", "policy", "preference", "definition", "remember", "memory", "must", "need")
        for claim in claims:
            if any(marker in claim["claim_text"].lower() for marker in durable_markers):
                return [memory_from_claim(claim, privacy_class)]
        return []


PROFILE = GeneralSourceReviewProfile(
    profile_id="general_source_review",
    display_name="General source review",
    version="0.1.0",
    purpose="Review source material without assuming a domain or promoting its contents.",
    allowed_input_types=("note", "text", "markdown", "other_safe_text"),
    claim_hints=("requirements", "reported results", "recommendations", "definitions", "decisions", "constraints"),
    uncertainty_rules=("label missing context", "separate source claims from Chaser agent inference"),
    action_policy=("propose local review steps only", "require human approval"),
    memory_policy=("default to no memory", "propose only apparently durable source-grounded candidates"),
    tags=("general", "source-review", "standalone"),
)
