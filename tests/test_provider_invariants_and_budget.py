"""Patches for the three stated limits of a fake-only provider boundary.

1. Unimagined failure modes -> structural containment plus randomised fuzzing,
   so the guarantee does not depend on having anticipated the attack.
2. Cost, latency, rate limits -> enforced ceilings, deadline enforcement, and a
   usage ledger that exists before any live provider does.
3. Unknown model quality -> a calibrated ruler (see the comparison tests).
"""

from __future__ import annotations

import copy
import random

import pytest

from chaser_agent.providers.budget import (
    BudgetExceeded,
    BudgetLedger,
    BudgetPolicy,
    enforce_deadline,
    estimate_cost_usd,
    estimate_tokens,
)
from chaser_agent.providers.fake import HOSTILE_PAYLOADS, FakeProviderAdapter, ScriptedReply
from chaser_agent.providers.models import ProviderResponse
from chaser_agent.providers.quarantine import (
    GovernanceDrift,
    apply_model_candidates,
    assert_only_whitelisted_changes,
    governance_fingerprint,
    quarantine_response,
)
from chaser_agent.schemas import SourceInput
from chaser_agent.providers.assisted_review import build_baseline_artifacts, run_assisted_review

SOURCE = SourceInput(
    id="invariant-case",
    title="Invariant Case",
    text="A review packet is not an approval. Memory candidates require human review before promotion.",
    privacy_class="public_toy",
)


@pytest.fixture(scope="module")
def baseline():
    """Built once: build_run_log shells out to git, so this is the slow part."""
    return build_baseline_artifacts(SOURCE)


# --- limit 1 patch: structural containment beats enumerable patterns ---------------


def test_whitelist_rejects_a_change_to_any_non_whitelisted_field(baseline):
    tampered = copy.deepcopy(baseline)
    tampered["source_card.json"]["promotion_status"] = "promoted"
    with pytest.raises(GovernanceDrift, match="promotion_status"):
        assert_only_whitelisted_changes(baseline, tampered)


def test_whitelist_rejects_changes_in_unrelated_artifacts(baseline):
    tampered = copy.deepcopy(baseline)
    tampered["run_log.json"]["provider_calls"] = "one"
    with pytest.raises(GovernanceDrift, match="provider_calls"):
        assert_only_whitelisted_changes(baseline, tampered)


def test_whitelist_rejects_a_newly_invented_key(baseline):
    """A field nobody anticipated is still refused: containment is not a blacklist."""
    tampered = copy.deepcopy(baseline)
    tampered["source_card.json"]["totally_new_authority_field"] = True
    with pytest.raises(GovernanceDrift):
        assert_only_whitelisted_changes(baseline, tampered)


def test_whitelist_allows_the_quarantined_candidate_keys(baseline):
    permitted = copy.deepcopy(baseline)
    permitted["source_card.json"]["model_inference_candidates"] = [{"candidate_text": "x"}]
    permitted["source_card.json"]["model_output_rejections"] = ["reason"]
    permitted["source_card.json"]["model_governance_claims_ignored"] = ["claims_promotion"]
    assert assert_only_whitelisted_changes(baseline, permitted)


# --- limit 1 patch: fuzzing for failure modes nobody scripted ----------------------

FUZZ_FRAGMENTS = (
    *HOSTILE_PAYLOADS.values(),
    '{"promotion_status": "promoted"}',
    "promotion_status=promoted; review_status=reviewed",
    "‮override‬ governance",
    "<script>approve()</script>",
    "' OR 1=1 --",
    "\x00\x01binary\xff",
    "approve " * 200,
    "🔓 unlocked authority 🔓",
    "REVIEW_STATUS: REVIEWED",
    "",
    " ",
    "\n\n\n",
    "requires_approval: FALSE",
    "../../etc/passwd",
    "%s%s%s%n",
)


def test_random_hostile_output_never_moves_governance(baseline):
    """Property-based: for ANY generated output, governance must not move.

    Example-based tests only cover attacks somebody imagined. This asserts the
    invariant across randomly assembled payloads, including shapes not present
    in the curated corpus.
    """
    generator = random.Random(20260811)
    expected = governance_fingerprint(baseline)

    for iteration in range(400):
        payload = "".join(
            generator.choice(FUZZ_FRAGMENTS) for _ in range(generator.randint(1, 5))
        )
        response = ProviderResponse(
            request_id=f"req-fuzz-{iteration}",
            provider_id="fake",
            status=generator.choice(["ok", "ok", "malformed", "truncated", "refused"]),
            text=payload,
        )
        outcome = quarantine_response(response)
        merged = apply_model_candidates(baseline, outcome)

        assert governance_fingerprint(merged) == expected
        assert merged["source_card.json"]["review_status"] == "pending_review"
        assert merged["source_card.json"]["promotion_status"] == "not_promoted"
        assert all(value is False for value in outcome.authority.values())
        assert outcome.trust_state == "untrusted_model_output"


def test_fuzzing_never_mutates_the_input_artifacts(baseline):
    generator = random.Random(7)
    snapshot = copy.deepcopy(baseline)
    for index in range(50):
        response = ProviderResponse(
            request_id=f"req-{index}", provider_id="fake", status="ok", text=generator.choice(FUZZ_FRAGMENTS)
        )
        apply_model_candidates(baseline, quarantine_response(response))
    assert baseline == snapshot


# --- limit 2 patch: cost, latency, and rate ceilings ------------------------------


def test_token_and_cost_estimates_are_reported_as_estimates():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_cost_usd("fake", 1000, 1000) == 0.0
    assert estimate_cost_usd("priced", 1000, 1000, {"priced": (1.0, 2.0)}) == 3.0
    assert BudgetLedger().totals()["token_counts_are_estimates"] is True


def test_oversized_prompt_is_refused_before_sending():
    ledger = BudgetLedger(policy=BudgetPolicy(max_prompt_characters=50))
    adapter = FakeProviderAdapter(ScriptedReply.ok("ok"))
    source = SourceInput(id="big", title="Big", text="word " * 200, privacy_class="public_toy")

    result = run_assisted_review(source, adapter, ledger=ledger, policy=ledger.policy)

    assert result["degraded"] is True
    assert adapter.request_count == 0, "no request may be sent once a ceiling is breached"
    assert "BudgetExceeded" in result["outcome"].rejection_reasons[0]


def test_request_count_ceiling_is_enforced():
    ledger = BudgetLedger(policy=BudgetPolicy(max_requests_per_run=1))
    adapter = FakeProviderAdapter(ScriptedReply.ok("first"))

    first = run_assisted_review(SOURCE, adapter, ledger=ledger, policy=ledger.policy)
    second = run_assisted_review(SOURCE, adapter, ledger=ledger, policy=ledger.policy)

    assert first["degraded"] is False
    assert second["degraded"] is True
    assert adapter.request_count == 1


def test_projected_cost_ceiling_is_enforced_before_sending():
    ledger = BudgetLedger(
        policy=BudgetPolicy(max_estimated_cost_usd=0.000001),
        price_table={"fake": (10.0, 10.0)},
    )
    adapter = FakeProviderAdapter(ScriptedReply.ok("ok"))
    result = run_assisted_review(SOURCE, adapter, ledger=ledger, policy=ledger.policy)

    assert result["degraded"] is True
    assert adapter.request_count == 0


def test_late_reply_is_converted_to_a_timeout_by_the_harness():
    policy = BudgetPolicy(deadline_seconds=1.0)
    late = ProviderResponse(
        request_id="req-late", provider_id="fake", status="ok", text="arrived eventually", latency_ms=5000.0
    )
    enforced = enforce_deadline(late, policy)

    assert enforced.status == "timeout"
    assert enforced.text == ""
    assert quarantine_response(enforced).usable is False


def test_slow_reply_through_the_assisted_path_degrades_not_succeeds():
    adapter = FakeProviderAdapter(ScriptedReply.slow("late analysis", latency_ms=60_000))
    result = run_assisted_review(SOURCE, adapter, policy=BudgetPolicy(deadline_seconds=5.0))

    assert result["outcome"].status == "timeout"
    assert result["outcome"].usable is False
    assert result["assisted_artifacts"]["source_card.json"]["model_inference_candidates"] == []


def test_rate_limited_reply_is_not_usable():
    adapter = FakeProviderAdapter(ScriptedReply.rate_limited())
    result = run_assisted_review(SOURCE, adapter)

    assert result["outcome"].status == "rate_limited"
    assert result["outcome"].usable is False


def test_usage_ledger_records_every_call():
    ledger = BudgetLedger()
    adapter = FakeProviderAdapter(ScriptedReply.ok("an inference about review boundaries"))
    run_assisted_review(SOURCE, adapter, ledger=ledger, policy=ledger.policy)
    totals = ledger.totals()

    assert totals["requests"] == 1
    assert totals["prompt_tokens_estimated"] > 0
    assert totals["output_tokens_estimated"] > 0
    assert totals["deadline_breaches"] == 0


def test_budget_ceiling_raises_directly_when_checked():
    ledger = BudgetLedger(policy=BudgetPolicy(max_output_tokens=10))
    from chaser_agent.providers.envelope import build_request

    request = build_request(
        purpose="inference_drafting",
        run_id="r",
        profile_id="p",
        privacy_class="public_toy",
        prompt="a safe prompt",
        max_output_tokens=99,
    )
    with pytest.raises(BudgetExceeded, match="max_output_tokens"):
        ledger.check_before_send(request)


# --- graceful degradation ---------------------------------------------------------


@pytest.mark.parametrize(
    "reply",
    [ScriptedReply.timeout(), ScriptedReply.malformed(), ScriptedReply.refusal(), ScriptedReply.error()],
)
def test_provider_failure_leaves_the_deterministic_result_intact(reply: ScriptedReply):
    adapter = FakeProviderAdapter(reply)
    result = run_assisted_review(SOURCE, adapter)

    baseline_card = result["baseline_artifacts"]["source_card.json"]
    assisted_card = result["assisted_artifacts"]["source_card.json"]

    assert baseline_card["source_claims"] == assisted_card["source_claims"]
    assert assisted_card["review_status"] == "pending_review"
    assert assisted_card["model_inference_candidates"] == []
