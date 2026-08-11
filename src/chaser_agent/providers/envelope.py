"""Build provider request envelopes and refuse unsafe ones before any send.

This is the privacy dry run: an envelope can be built and inspected without a
provider existing, so "what would we have sent to a third party?" is answerable
and testable before a live provider is ever approved.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from chaser_agent.providers.models import SENDABLE_PRIVACY_CLASSES, ProviderRequest

# Patterns that must never leave the machine inside a prompt.
SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{12,}")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}")),
    ("assigned_credential", re.compile(r"(?i)\b(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*\S+")),
    ("windows_user_path", re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+")),
    ("unix_home_path", re.compile(r"/(?:home|Users)/[^/\s]+")),
)


class EnvelopeRefused(Exception):
    """Raised when an envelope must not be sent to any provider."""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def scan_for_sensitive_material(text: str) -> list[str]:
    """Return the names of sensitive patterns found in text."""
    return sorted({name for name, pattern in SENSITIVE_PATTERNS if pattern.search(text)})


def make_request_id(purpose: str, run_id: str, prompt: str, created_at: str) -> str:
    seed = f"{purpose}\0{run_id}\0{prompt}\0{created_at}"
    return "req-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]


def assert_envelope_is_sendable(request: ProviderRequest) -> None:
    """Fail closed if an envelope carries disallowed privacy class or secrets."""
    if request.privacy_class not in SENDABLE_PRIVACY_CLASSES:
        raise EnvelopeRefused(
            f"privacy_class {request.privacy_class!r} may not be sent to a provider; "
            f"sendable: {', '.join(sorted(SENDABLE_PRIVACY_CLASSES))}"
        )
    findings = scan_for_sensitive_material(request.prompt)
    if findings:
        raise EnvelopeRefused(f"envelope contains sensitive material: {', '.join(findings)}")


def build_request(
    *,
    purpose: str,
    run_id: str,
    profile_id: str,
    privacy_class: str,
    prompt: str,
    created_at: str | None = None,
    max_output_tokens: int = 1024,
    metadata: dict[str, Any] | None = None,
) -> ProviderRequest:
    """Build an envelope and refuse it immediately if it is unsafe to send."""
    stamped_at = created_at or utc_now_iso()
    request = ProviderRequest(
        request_id=make_request_id(purpose, run_id, prompt, stamped_at),
        purpose=purpose,
        run_id=run_id,
        profile_id=profile_id,
        privacy_class=privacy_class,
        prompt=prompt,
        created_at=stamped_at,
        max_output_tokens=max_output_tokens,
        metadata=dict(metadata or {}),
    )
    assert_envelope_is_sendable(request)
    return request


def describe_envelope(request: ProviderRequest) -> dict[str, Any]:
    """Human-inspectable summary: exactly what a provider would receive."""
    return {
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "purpose": request.purpose,
        "run_id": request.run_id,
        "profile_id": request.profile_id,
        "privacy_class": request.privacy_class,
        "prompt_characters": len(request.prompt),
        "prompt": request.prompt,
        "max_output_tokens": request.max_output_tokens,
        "sensitive_findings": scan_for_sensitive_material(request.prompt),
        "would_send_to": "no provider is active in P0.1",
        "network_call_performed": False,
    }
