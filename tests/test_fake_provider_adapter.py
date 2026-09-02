"""Boundary tests for the provider-neutral inference seam.

These use a scripted fake so the adversarial cases are deterministic: the model
emits forged approvals, injected instructions, and malformed payloads on demand,
every run, and the harness must hold every time.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chaser_agent.providers.envelope import (
    EnvelopeRefused,
    assert_envelope_is_sendable,
    build_request,
    describe_envelope,
    scan_for_sensitive_material,
)
from chaser_agent.providers.fake import HOSTILE_PAYLOADS, FakeProviderAdapter, ScriptedReply
from chaser_agent.providers.models import ProviderRequest
from chaser_agent.providers.quarantine import (
    GovernanceDrift,
    apply_model_candidates,
    detect_governance_claims,
    governance_fingerprint,
    quarantine_response,
)
from chaser_agent.run_artifacts import build_run_log
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts

SAFE_PROMPT = "Summarise the claims in this public note about review boundaries."


def make_request(prompt: str = SAFE_PROMPT, privacy_class: str = "public_toy") -> ProviderRequest:
    return build_request(
        purpose="inference_drafting",
        run_id="run-001",
        profile_id="general_source_review",
        privacy_class=privacy_class,
        prompt=prompt,
        created_at="1970-01-01T00:00:00Z",
    )


def baseline_artifacts() -> dict:
    source = SourceInput(
        id="provider-boundary-case",
        title="Provider Boundary Case",
        text="A review packet is not an approval. Memory candidates require human review.",
        privacy_class="public_toy",
    )
    artifacts = build_source_card_artifacts(source, Path("case.md"), "run-001", "1970-01-01T00:00:00Z")
    artifacts["run_log.json"] = build_run_log(
        run_id="run-001",
        created_at="1970-01-01T00:00:00Z",
        command="test",
        input_source_id=source.id,
        output_paths=[Path("run_log.json")],
    )
    return artifacts


# --- envelope: the privacy dry run -------------------------------------------------


def test_request_id_and_hash_are_deterministic():
    assert make_request().request_id == make_request().request_id
    assert make_request().request_hash == make_request().request_hash


def test_envelope_refuses_prompt_containing_a_credential():
    with pytest.raises(EnvelopeRefused, match="sensitive material"):
        make_request(prompt="Use this key sk-abcdefghijklmnop12345 to authenticate.")


def test_envelope_refuses_disallowed_privacy_class():
    with pytest.raises(EnvelopeRefused, match="privacy_class"):
        make_request(privacy_class="private")


@pytest.mark.parametrize(
    "prompt, expected",
    [
        ("token: ghp_abcdefghijklmnopqrst", "github_token"),
        ("-----BEGIN RSA PRIVATE KEY-----", "private_key_block"),
        ("api_key = supersecretvalue", "assigned_credential"),
        # Synthetic path only. Never put a real local path in a public repo,
        # even as test data.
        ("open " + "C:" + chr(92) + "Users" + chr(92) + "example" + chr(92) + "vault.md", "windows_user_path"),
    ],
)
def test_sensitive_scanner_detects_known_shapes(prompt: str, expected: str):
    assert expected in scan_for_sensitive_material(prompt)


def test_envelope_can_be_inspected_without_sending_anything():
    described = describe_envelope(make_request())
    assert described["network_call_performed"] is False
    assert described["sensitive_findings"] == []
    assert described["prompt"] == SAFE_PROMPT


def test_unsupported_purpose_is_rejected():
    with pytest.raises(ValueError, match="unsupported provider purpose"):
        build_request(
            purpose="promote_memory",
            run_id="run-001",
            profile_id="general_source_review",
            privacy_class="public_toy",
            prompt=SAFE_PROMPT,
        )


# --- fake adapter behaviour --------------------------------------------------------


def test_fake_adapter_is_deterministic_and_makes_no_network_call():
    adapter = FakeProviderAdapter(ScriptedReply.ok("Two claims relate to review boundaries."))
    first = adapter.complete(make_request())
    second = adapter.complete(make_request())

    assert adapter.network_access is False
    assert adapter.is_fake is True
    assert first.text == second.text
    assert first.network_call_performed is False
    assert adapter.request_count == 2


def test_fake_adapter_records_exactly_what_would_have_been_sent():
    adapter = FakeProviderAdapter(ScriptedReply.ok("ok"))
    adapter.complete(make_request())
    sent = adapter.last_request()

    assert sent is not None
    assert sent.prompt == SAFE_PROMPT
    assert scan_for_sensitive_material(sent.prompt) == []


def test_fake_adapter_enforces_the_pre_send_gate():
    adapter = FakeProviderAdapter(ScriptedReply.ok("ok"))
    unsafe = ProviderRequest(
        request_id="req-unsafe",
        purpose="inference_drafting",
        run_id="run-001",
        profile_id="general_source_review",
        privacy_class="private",
        prompt=SAFE_PROMPT,
        created_at="1970-01-01T00:00:00Z",
    )
    with pytest.raises(EnvelopeRefused):
        adapter.complete(unsafe)
    assert adapter.request_count == 0


def test_scripted_replies_can_be_selected_per_purpose():
    adapter = FakeProviderAdapter(
        {"inference_drafting": ScriptedReply.ok("inference"), "summary_drafting": ScriptedReply.timeout()}
    )
    assert adapter.complete(make_request()).status == "ok"


# --- failure handling: never a silent success --------------------------------------


@pytest.mark.parametrize(
    "reply, status",
    [
        (ScriptedReply.timeout(), "timeout"),
        (ScriptedReply.malformed(), "malformed"),
        (ScriptedReply.truncated(), "truncated"),
        (ScriptedReply.refusal(), "refused"),
        (ScriptedReply.error(), "error"),
    ],
)
def test_non_ok_replies_are_never_usable(reply: ScriptedReply, status: str):
    adapter = FakeProviderAdapter(reply)
    outcome = quarantine_response(adapter.complete(make_request()))

    assert outcome.status == status
    assert outcome.usable is False
    assert outcome.candidate_text == ""
    assert outcome.rejection_reasons


def test_empty_ok_response_is_not_usable():
    adapter = FakeProviderAdapter(ScriptedReply.ok("   "))
    outcome = quarantine_response(adapter.complete(make_request()))
    assert outcome.usable is False


# --- the adversarial core ----------------------------------------------------------


@pytest.mark.parametrize("payload_name", sorted(HOSTILE_PAYLOADS))
def test_every_hostile_payload_is_detected_and_refused_authority(payload_name: str):
    adapter = FakeProviderAdapter(ScriptedReply.hostile(payload_name))
    outcome = quarantine_response(adapter.complete(make_request()))

    assert outcome.governance_claims_ignored, f"{payload_name} claimed authority undetected"
    assert outcome.usable is False
    assert outcome.trust_state == "untrusted_model_output"
    assert all(granted is False for granted in outcome.authority.values())


@pytest.mark.parametrize("payload_name", sorted(HOSTILE_PAYLOADS))
def test_hostile_model_output_cannot_move_any_governance_field(payload_name: str):
    """The headline guarantee: a hostile reply changes nothing that governs."""
    artifacts = baseline_artifacts()
    before = governance_fingerprint(artifacts)

    adapter = FakeProviderAdapter(ScriptedReply.hostile(payload_name))
    outcome = quarantine_response(adapter.complete(make_request()))
    merged = apply_model_candidates(artifacts, outcome)

    assert governance_fingerprint(merged) == before
    assert merged["source_card.json"]["review_status"] == "pending_review"
    assert merged["source_card.json"]["promotion_status"] == "not_promoted"
    assert merged["source_card.json"]["model_inference_candidates"] == []
    assert merged["source_card.json"]["model_governance_claims_ignored"]


def test_usable_output_lands_as_a_quarantined_candidate_not_an_inference():
    artifacts = baseline_artifacts()
    deterministic_inferences = list(artifacts["source_card.json"]["chaser_agent_inferences"])

    adapter = FakeProviderAdapter(ScriptedReply.ok("The two claims may both bear on review boundaries."))
    outcome = quarantine_response(adapter.complete(make_request()))
    merged = apply_model_candidates(artifacts, outcome)

    assert outcome.usable is True
    # Deterministic inference is untouched; model text is kept separate.
    assert merged["source_card.json"]["chaser_agent_inferences"] == deterministic_inferences
    candidate = merged["source_card.json"]["model_inference_candidates"][0]
    assert candidate["origin"] == "model_candidate"
    assert candidate["trust_state"] == "untrusted_model_output"
    assert candidate["confidence"] == "unverified"
    assert candidate["requires_human_verification"] is True
    assert candidate["promotion_status"] == "not_promoted"


def test_original_artifacts_are_not_mutated_by_merging():
    artifacts = baseline_artifacts()
    adapter = FakeProviderAdapter(ScriptedReply.ok("A candidate inference."))
    outcome = quarantine_response(adapter.complete(make_request()))
    apply_model_candidates(artifacts, outcome)

    assert "model_inference_candidates" not in artifacts["source_card.json"]


def test_governance_drift_is_raised_rather_than_persisted():
    """Defence in depth: if a future merge moved a governed field, it must fail loudly."""
    artifacts = baseline_artifacts()
    outcome = quarantine_response(FakeProviderAdapter(ScriptedReply.ok("text")).complete(make_request()))

    original = governance_fingerprint

    def drifting_fingerprint(values, _calls={"n": 0}):  # noqa: B006 - test double
        _calls["n"] += 1
        result = dict(original(values))
        if _calls["n"] > 1:
            result["source_card.json:promotion_status"] = "promoted"
        return result

    import chaser_agent.providers.quarantine as quarantine_module

    quarantine_module.governance_fingerprint = drifting_fingerprint
    try:
        with pytest.raises(GovernanceDrift):
            apply_model_candidates(artifacts, outcome)
    finally:
        quarantine_module.governance_fingerprint = original


def test_plain_analysis_text_is_not_flagged_as_a_governance_claim():
    """The detector must not fire on ordinary review language."""
    assert detect_governance_claims("The source separates claims from inference and notes two uncertainties.") == []
