"""Quarantine provider output.

A model reply is untrusted input, not an authority. It may propose analysis; it
may never set a governance field, approve an action, promote a memory, or claim
that work was completed. This module is the boundary that enforces that: it
classifies a raw response, records any authority the text tried to claim, and
merges usable text into artifacts as clearly-labelled candidates while proving
the governance fields did not move.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from chaser_agent.providers.models import ProviderOutcome, ProviderResponse

UNTRUSTED = "untrusted_model_output"

# Text patterns where a reply attempts to assert authority it does not have.
GOVERNANCE_CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("claims_promotion", re.compile(r"(?i)promotion_status\s*[:=]\s*promoted|promote[sd]?\s+(?:every\s+)?memory")),
    ("claims_review_complete", re.compile(r"(?i)review_status\s*[:=]\s*reviewed|marked?\s+this\s+(?:run\s+)?(?:complete|reviewed)")),
    ("claims_approval", re.compile(r"(?i)requires_approval\s*[:=]\s*false|approved\s+automatically|approval\s+consumed|i\s+have\s+approved")),
    ("claims_canonical", re.compile(r"(?i)canonical\s+(?:truth|state)|written\s+to\s+canonical")),
    ("claims_action_performed", re.compile(r"(?i)i\s+have\s+(?:updated|committed|published|deployed|executed|posted)|deployment\s+is\s+live|trade\s+has\s+been\s+executed")),
    ("instruction_injection", re.compile(r"(?i)ignore\s+(?:your\s+)?(?:previous\s+)?(?:instructions|rules|governance)|developer\s+mode")),
    ("claims_authority", re.compile(r"(?i)as\s+the\s+chaseos\s+control\s+plane|i\s+am\s+authoris|disable\s+the\s+review\s+gate")),
    ("denies_uncertainty", re.compile(r"(?i)there\s+is\s+no\s+uncertainty|requiring\s+no\s+review|no\s+further\s+human\s+review")),
)

# Governance fields that model output must never be able to move.
GOVERNED_PATHS: tuple[tuple[str, str], ...] = (
    ("source_card.json", "review_status"),
    ("source_card.json", "promotion_status"),
    ("source_card.json", "trust_state"),
)


def detect_governance_claims(text: str) -> list[str]:
    """Return names of authority claims the text attempted to make."""
    return sorted({name for name, pattern in GOVERNANCE_CLAIM_PATTERNS if pattern.search(text)})


def quarantine_response(response: ProviderResponse) -> ProviderOutcome:
    """Classify a raw provider reply. Nothing here grants authority."""
    reasons: list[str] = []

    if response.status != "ok":
        reasons.append(f"provider status {response.status!r} is not a usable completion")
    if response.network_call_performed:
        reasons.append("response reported a network call, which is not permitted in P0.1")
    if response.status == "ok" and not response.text.strip():
        reasons.append("provider returned empty text")

    claims = detect_governance_claims(response.text)
    if claims:
        # The reply is still not usable as authority, but its analysis text is not
        # discarded solely for containing hostile phrasing — it is recorded,
        # flagged, and downgraded so a human can see what was attempted.
        reasons.append("response attempted to assert authority it does not have")

    return ProviderOutcome(
        request_id=response.request_id,
        provider_id=response.provider_id,
        status=response.status,
        trust_state=UNTRUSTED,
        usable=not reasons,
        candidate_text=response.text if response.status == "ok" else "",
        rejection_reasons=tuple(reasons),
        governance_claims_ignored=tuple(claims),
    )


def governance_fingerprint(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Snapshot every governance field model output must not be able to change."""
    fingerprint: dict[str, Any] = {}
    for artifact_name, field_name in GOVERNED_PATHS:
        artifact = artifacts.get(artifact_name)
        if isinstance(artifact, dict) and field_name in artifact:
            fingerprint[f"{artifact_name}:{field_name}"] = artifact[field_name]

    actions = artifacts.get("action_candidates.json")
    if isinstance(actions, dict):
        fingerprint["action_candidates.json:requires_approval"] = [
            action.get("requires_approval") for action in actions.get("action_candidates", [])
        ]

    memories = artifacts.get("memory_candidates.json")
    if isinstance(memories, dict):
        fingerprint["memory_candidates.json:promotion_status"] = [
            memory.get("promotion_status") for memory in memories.get("memory_candidates", [])
        ]

    run_log = artifacts.get("run_log.json")
    if isinstance(run_log, dict):
        fingerprint["run_log.json:authority"] = {
            key: run_log[key]
            for key in (
                "provider_calls",
                "external_api_calls",
                "runtime_adapters",
                "mcp_activation",
                "browser_or_computer_use",
                "fine_tuning_or_training",
                "review_required",
            )
            if key in run_log
        }
    return fingerprint


class GovernanceDrift(Exception):
    """Raised if merging model output would change a governance field."""


def apply_model_candidates(artifacts: dict[str, Any], outcome: ProviderOutcome) -> dict[str, Any]:
    """Return new artifacts with model output added as a quarantined candidate.

    Model text is never merged into `chaser_agent_inferences`; it lands in a
    separate `model_inference_candidates` list so deterministic inference and
    untrusted model proposals can never be confused. Governance fields are
    fingerprinted before and after, and any drift raises rather than persisting.
    """
    before = governance_fingerprint(artifacts)
    merged = copy.deepcopy(artifacts)

    card = merged.get("source_card.json")
    if isinstance(card, dict):
        candidates = list(card.get("model_inference_candidates", []))
        if outcome.usable and outcome.candidate_text.strip():
            candidates.append(
                {
                    "candidate_id": f"model-inference-{len(candidates) + 1:03d}",
                    "candidate_text": outcome.candidate_text,
                    "origin": "model_candidate",
                    "provider_id": outcome.provider_id,
                    "request_id": outcome.request_id,
                    "trust_state": UNTRUSTED,
                    "confidence": "unverified",
                    "requires_human_verification": True,
                    "promotion_status": "not_promoted",
                }
            )
        card["model_inference_candidates"] = candidates
        card["model_output_rejections"] = list(outcome.rejection_reasons)
        card["model_governance_claims_ignored"] = list(outcome.governance_claims_ignored)

    after = governance_fingerprint(merged)
    if before != after:
        raise GovernanceDrift(f"model output changed governance fields: {before!r} -> {after!r}")
    return merged
