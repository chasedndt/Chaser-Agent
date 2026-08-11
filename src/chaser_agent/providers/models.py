"""Provider request/response envelopes and quarantined outcomes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProviderStatus = Literal["ok", "refused", "timeout", "malformed", "truncated", "error"]
PROVIDER_STATUSES: tuple[ProviderStatus, ...] = ("ok", "refused", "timeout", "malformed", "truncated", "error")

# Least authority: a provider may only be asked to analyse. There is deliberately
# no purpose for executing an action, promoting memory, approving work, or
# granting authority — those are governance decisions and are not model-shaped.
ALLOWED_PURPOSES: frozenset[str] = frozenset(
    {
        "claim_extraction",
        "inference_drafting",
        "uncertainty_labeling",
        "contradiction_check",
        "summary_drafting",
    }
)

# Privacy classes an envelope may carry to a provider at all. Anything else is
# refused before a request is built, not filtered afterwards.
SENDABLE_PRIVACY_CLASSES: frozenset[str] = frozenset({"public_toy", "public", "scrubbed"})


@dataclass(frozen=True)
class ProviderRequest:
    """What would be sent to a provider. Inspectable before anything is sent."""

    request_id: str
    purpose: str
    run_id: str
    profile_id: str
    privacy_class: str
    prompt: str
    created_at: str
    max_output_tokens: int = 1024
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.purpose not in ALLOWED_PURPOSES:
            raise ValueError(
                f"unsupported provider purpose: {self.purpose}; allowed: {', '.join(sorted(ALLOWED_PURPOSES))}"
            )
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def request_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProviderResponse:
    """Raw adapter reply. Untrusted until quarantined."""

    request_id: str
    provider_id: str
    status: ProviderStatus
    text: str = ""
    error: str | None = None
    is_fake: bool = True
    network_call_performed: bool = False

    def __post_init__(self) -> None:
        if self.status not in PROVIDER_STATUSES:
            raise ValueError(f"invalid provider status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderOutcome:
    """A quarantined response: candidate analysis text with zero authority."""

    request_id: str
    provider_id: str
    status: ProviderStatus
    trust_state: str
    usable: bool
    candidate_text: str
    rejection_reasons: tuple[str, ...] = ()
    governance_claims_ignored: tuple[str, ...] = ()

    @property
    def authority(self) -> dict[str, bool]:
        return {
            "promote_memory": False,
            "approve_action": False,
            "execute_action": False,
            "mutate_review_status": False,
            "mutate_promotion_status": False,
            "consume_approval": False,
            "mutate_canonical_state": False,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authority"] = self.authority
        return payload
