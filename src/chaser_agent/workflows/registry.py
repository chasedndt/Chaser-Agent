"""Explicit P0.1 profile registry."""

from __future__ import annotations

from chaser_agent.core.protocols import WorkflowProfile
from chaser_agent.workflows.ai_engineering_research_review import PROFILE as AI_ENGINEERING_RESEARCH_REVIEW
from chaser_agent.workflows.general_source_review import PROFILE as GENERAL_SOURCE_REVIEW
from chaser_agent.workflows.website_design_review import PROFILE as WEBSITE_DESIGN_REVIEW


_PROFILES: dict[str, WorkflowProfile] = {
    profile.profile_id: profile
    for profile in (
        GENERAL_SOURCE_REVIEW,
        AI_ENGINEERING_RESEARCH_REVIEW,
        WEBSITE_DESIGN_REVIEW,
    )
}


def get_profile(profile_id: str = "general_source_review") -> WorkflowProfile:
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(_PROFILES))
        raise ValueError(f"unknown workflow profile {profile_id!r}; choose one of: {available}") from exc


def list_profiles() -> tuple[WorkflowProfile, ...]:
    return tuple(_PROFILES[profile_id] for profile_id in sorted(_PROFILES))
