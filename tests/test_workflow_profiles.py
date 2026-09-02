from __future__ import annotations

import ast
from pathlib import Path

import pytest

from chaser_agent.core.protocols import WorkflowProfile
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts, extract_claims
from chaser_agent.workflows import get_profile, list_profiles


def _build(text: str, profile_id: str = "general_source_review") -> dict:
    source = SourceInput(id="source-1", title="Source", text=text)
    return build_source_card_artifacts(
        source,
        Path("source.md"),
        run_id="run-1",
        created_at="1970-01-01T00:00:00Z",
        profile_id=profile_id,
    )["source_card.json"]


def test_required_profiles_are_explicit_and_general_is_default():
    profiles = {profile.profile_id: profile for profile in list_profiles()}

    assert set(profiles) == {
        "general_source_review",
        "ai_engineering_research_review",
        "website_design_review",
    }
    assert get_profile() is profiles["general_source_review"]
    assert all(isinstance(profile, WorkflowProfile) for profile in profiles.values())


def test_profile_contract_fields_are_populated():
    required = (
        "profile_id",
        "display_name",
        "version",
        "purpose",
        "allowed_input_types",
        "claim_hints",
        "uncertainty_rules",
        "action_policy",
        "memory_policy",
        "forbidden_actions",
        "required_review_dimensions",
        "tags",
    )

    for profile in list_profiles():
        assert all(getattr(profile, field) for field in required)


def test_heading_is_not_emitted_as_a_claim():
    claims, evidence = extract_claims("# Architecture\n\nThe service must remain local.\n", "public_toy")

    assert [claim["claim_text"] for claim in claims] == ["The service must remain local."]
    assert evidence[0]["text"] == "The service must remain local."


def test_general_profile_has_no_unprompted_design_or_media_boilerplate():
    card = _build("The operator must review every durable policy change.")
    authored = " ".join(
        [item["inference_text"] for item in card["chaser_agent_inferences"]]
        + [item["action_text"] for item in card["action_candidates"]]
        + [item["explanation"] for item in card["uncertainty_labels"]]
    ).lower()

    assert card["workflow_profile"] == "general_source_review"
    assert "website" not in authored
    assert "screenshot" not in authored
    assert "video" not in authored


def test_domain_behaviour_isolated_to_explicit_profiles():
    ai_card = _build("A study reported a benchmark improvement.", "ai_engineering_research_review")
    website_card = _build("The hero needs stronger contrast.", "website_design_review")

    assert ai_card["workflow_profile"] == "ai_engineering_research_review"
    assert "production truth" in ai_card["chaser_agent_inferences"][0]["inference_text"]
    assert website_card["workflow_profile"] == "website_design_review"
    assert "visual_context_required" in {row["label"] for row in website_card["uncertainty_labels"]}


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown workflow profile"):
        get_profile("not-a-profile")


def test_core_package_has_no_chaseos_import_dependency():
    core_root = Path("src/chaser_agent/core")
    imported_modules: list[str] = []
    for path in core_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

    assert not [name for name in imported_modules if name.lower().startswith("chaseos")]
