"""Layer 13 boundary: least authority, default deny, scoped targets, no execution.

Tools are the dangerous surface. A model reply is text; a tool call touches the
filesystem, the network, accounts, and money. These tests assert the denials,
because a boundary is only real if it refuses.
"""

from __future__ import annotations

import pytest

from chaser_agent.tools.fake import HOSTILE_TOOL_RESULTS, FakeToolAdapter, ScriptedToolReply
from chaser_agent.tools.models import ToolCapability, ToolRequest
from chaser_agent.tools.quarantine import detect_injection_signals, quarantine_tool_result
from chaser_agent.tools.registry import ToolDenied, ToolRegistry, target_within_scopes

READ_DOCS = ToolCapability(
    tool_id="read_docs",
    display_name="Read repository docs",
    purpose="Read public documentation files for review context.",
    side_effect_class="read_only",
    allowed_scopes=("docs/",),
    max_calls_per_run=2,
)
FETCH_BLOG = ToolCapability(
    tool_id="fetch_blog",
    display_name="Fetch a public blog page",
    purpose="Read a declared public research source.",
    side_effect_class="read_only",
    allowed_scopes=("https://blog.cloudflare.com/",),
)
WRITE_FILE = ToolCapability(
    tool_id="write_file",
    display_name="Write a local file",
    purpose="Declared for contract testing; not permitted in P0.1.",
    side_effect_class="local_write",
    allowed_scopes=("logs/",),
)
POST_TWEET = ToolCapability(
    tool_id="post_tweet",
    display_name="Publish a post",
    purpose="Declared for contract testing; not permitted in P0.1.",
    side_effect_class="external_effect",
    allowed_scopes=("https://x.com/",),
)


def registry_with(*capabilities: ToolCapability, grant: tuple[str, ...] = ()) -> ToolRegistry:
    registry = ToolRegistry()
    for capability in capabilities:
        registry.register(capability)
    for tool_id in grant:
        registry.grant(tool_id)
    return registry


def request(tool_id: str, target: str) -> ToolRequest:
    return ToolRequest(tool_id=tool_id, target=target, run_id="run-001", purpose="review context")


# --- capability declaration --------------------------------------------------------


def test_capability_must_declare_a_scope():
    with pytest.raises(ValueError, match="allowed scope"):
        ToolCapability(
            tool_id="x", display_name="x", purpose="x", side_effect_class="read_only", allowed_scopes=()
        )


def test_capability_rejects_unknown_side_effect_class():
    with pytest.raises(ValueError, match="side_effect_class"):
        ToolCapability(
            tool_id="x",
            display_name="x",
            purpose="x",
            side_effect_class="sudo",  # type: ignore[arg-type]
            allowed_scopes=("docs/",),
        )


def test_capability_is_frozen_so_authority_cannot_be_widened_in_place():
    with pytest.raises(Exception):
        READ_DOCS.allowed_scopes = ("/",)  # type: ignore[misc]


# --- default deny ------------------------------------------------------------------


def test_unregistered_tool_is_denied():
    registry = ToolRegistry()
    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request("read_docs", "docs/a.md"))
    assert denial.value.reason_code == "unregistered_tool"


def test_registration_alone_is_not_permission():
    """Declaring a capability describes a tool; it does not enable it."""
    registry = registry_with(READ_DOCS)
    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request("read_docs", "docs/a.md"))
    assert denial.value.reason_code == "tool_not_granted"


def test_granting_an_unknown_tool_is_refused():
    with pytest.raises(ToolDenied) as denial:
        ToolRegistry().grant("ghost")
    assert denial.value.reason_code == "unregistered_tool"


def test_granted_read_only_tool_inside_scope_is_authorized():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    assert registry.authorize(request("read_docs", "docs/01_Product/a.md")).tool_id == "read_docs"


def test_revoking_a_grant_restores_denial():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    registry.revoke("read_docs")
    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request("read_docs", "docs/a.md"))
    assert denial.value.reason_code == "tool_not_granted"


# --- scope containment -------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [
        "src/chaser_agent/cli.py",
        "docs/../src/secrets.py",
        "docs/../../etc/passwd",
        "../outside.md",
        "/etc/passwd",
        "https://evil.example.com/docs/a.md",
    ],
)
def test_targets_outside_scope_are_denied(target: str):
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request("read_docs", target))
    assert denial.value.reason_code == "scope_violation"


def test_path_traversal_cannot_escape_via_normalisation():
    assert target_within_scopes("docs/a/../b.md", ("docs/",)) is True
    assert target_within_scopes("docs/../../secret", ("docs/",)) is False


def test_url_scope_matches_host_and_path_prefix_only():
    registry = registry_with(FETCH_BLOG, grant=("fetch_blog",))
    assert registry.authorize(request("fetch_blog", "https://blog.cloudflare.com/monetization-gateway/"))
    for bad in ("https://blog.cloudflare.com.evil.test/x", "http://other.example.com/", "not-a-url"):
        with pytest.raises(ToolDenied):
            registry.authorize(request("fetch_blog", bad))


# --- side-effect gating ------------------------------------------------------------


@pytest.mark.parametrize("capability", [WRITE_FILE, POST_TWEET])
def test_side_effecting_tools_are_never_permitted_in_p0_1(capability: ToolCapability):
    registry = registry_with(capability, grant=(capability.tool_id,))
    target = capability.allowed_scopes[0] + "thing"
    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request(capability.tool_id, target))
    assert denial.value.reason_code == "side_effect_not_permitted"


# --- call budget -------------------------------------------------------------------


def test_call_budget_is_enforced_per_run():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    assert registry.plan(request("read_docs", "docs/a.md")).authorized
    assert registry.plan(request("read_docs", "docs/b.md")).authorized
    third = registry.plan(request("read_docs", "docs/c.md"))
    assert third.authorized is False
    assert third.denial_reason == "call_budget_exceeded"


def test_denied_calls_do_not_consume_budget():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    for _ in range(5):
        registry.plan(request("read_docs", "src/outside.py"))
    assert registry.plan(request("read_docs", "docs/a.md")).authorized is True


# --- no execution ------------------------------------------------------------------


def test_execution_is_not_available_and_raises():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    with pytest.raises(ToolDenied) as denial:
        registry.execute(request("read_docs", "docs/a.md"))
    assert denial.value.reason_code == "execution_not_implemented"


def test_authorized_plan_records_that_nothing_ran():
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    plan = registry.plan(request("read_docs", "docs/a.md")).to_dict()

    assert plan["authorized"] is True
    assert plan["executed"] is False
    assert all(value is False for value in plan["authority"].values())


def test_fake_adapter_performs_no_side_effects():
    adapter = FakeToolAdapter(ScriptedToolReply.ok("file contents"))
    result = adapter.call(request("read_docs", "docs/a.md"))

    assert adapter.performs_side_effects is False
    assert result.executed is False
    assert result.is_fake is True


# --- hostile tool output -----------------------------------------------------------


@pytest.mark.parametrize("payload_name", sorted(HOSTILE_TOOL_RESULTS))
def test_hostile_tool_output_is_detected_and_refused_authority(payload_name: str):
    adapter = FakeToolAdapter(ScriptedToolReply.hostile(payload_name))
    outcome = quarantine_tool_result(adapter.call(request("read_docs", "docs/a.md")))

    assert outcome.injection_signals, f"{payload_name} went undetected"
    assert outcome.usable is False
    assert outcome.trust_state == "untrusted_tool_output"
    assert all(granted is False for granted in outcome.authority.values())


def test_hostile_tool_output_cannot_widen_a_scope():
    """A result asking for a wider scope changes nothing about what is authorized."""
    registry = registry_with(READ_DOCS, grant=("read_docs",))
    adapter = FakeToolAdapter(ScriptedToolReply.hostile("scope_widening"))
    quarantine_tool_result(adapter.call(request("read_docs", "docs/a.md")))

    with pytest.raises(ToolDenied) as denial:
        registry.authorize(request("read_docs", "docs/../../etc/passwd"))
    assert denial.value.reason_code == "scope_violation"
    assert registry.capability("read_docs").allowed_scopes == ("docs/",)


@pytest.mark.parametrize("reply", [ScriptedToolReply.error(), ScriptedToolReply.timeout()])
def test_failed_tool_results_are_never_usable(reply: ScriptedToolReply):
    adapter = FakeToolAdapter(reply)
    outcome = quarantine_tool_result(adapter.call(request("read_docs", "docs/a.md")))

    assert outcome.usable is False
    assert outcome.content == ""


def test_benign_tool_output_is_usable_and_not_flagged():
    adapter = FakeToolAdapter(ScriptedToolReply.ok("The document describes the review boundary."))
    outcome = quarantine_tool_result(adapter.call(request("read_docs", "docs/a.md")))

    assert outcome.usable is True
    assert outcome.injection_signals == ()
    assert detect_injection_signals("A normal sentence about review packets.") == []
