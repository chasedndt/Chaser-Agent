"""Tool capability declarations, requests, results, and quarantined outcomes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

# A tool's side effects decide how much scrutiny it needs, so the class is part
# of its declaration rather than something inferred at call time.
SideEffectClass = Literal["read_only", "local_write", "external_effect"]
SIDE_EFFECT_CLASSES: tuple[SideEffectClass, ...] = ("read_only", "local_write", "external_effect")

# P0.1 permits planning read-only calls only. Local writes and external effects
# are declarable so contracts can be written and tested now, but they can never
# be authorized until an operator-approved grant path exists.
PERMITTED_SIDE_EFFECTS_P0_1: frozenset[str] = frozenset({"read_only"})


@dataclass(frozen=True)
class ToolCapability:
    """What a tool declares about itself. Authority comes from this, not from code."""

    tool_id: str
    display_name: str
    purpose: str
    side_effect_class: SideEffectClass
    allowed_scopes: tuple[str, ...]
    max_calls_per_run: int = 5
    requires_approval: bool = True
    reversible: bool = False

    def __post_init__(self) -> None:
        if not self.tool_id.strip():
            raise ValueError("tool_id is required")
        if self.side_effect_class not in SIDE_EFFECT_CLASSES:
            raise ValueError(f"invalid side_effect_class: {self.side_effect_class}")
        if not self.allowed_scopes:
            raise ValueError("a capability must declare at least one allowed scope")
        if self.max_calls_per_run <= 0:
            raise ValueError("max_calls_per_run must be positive")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolRequest:
    tool_id: str
    target: str
    run_id: str
    purpose: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError("target is required")

    @property
    def request_hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return "toolreq-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class ToolResult:
    """Raw result a tool would return. Untrusted until quarantined."""

    tool_id: str
    request_hash: str
    status: Literal["ok", "error", "denied", "timeout"]
    content: str = ""
    error: str | None = None
    is_fake: bool = True
    executed: bool = False


@dataclass(frozen=True)
class ToolInvocationPlan:
    """An authorized call that was deliberately not executed."""

    request_hash: str
    tool_id: str
    target: str
    side_effect_class: SideEffectClass
    authorized: bool
    executed: bool = False
    denial_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authority"] = {
            "execute_performed": False,
            "filesystem_write_performed": False,
            "network_call_performed": False,
            "credential_access_performed": False,
            "approval_consumed": False,
        }
        return payload


@dataclass(frozen=True)
class ToolOutcome:
    """A quarantined tool result: content with zero authority."""

    tool_id: str
    request_hash: str
    status: str
    trust_state: str
    usable: bool
    content: str
    rejection_reasons: tuple[str, ...] = ()
    injection_signals: tuple[str, ...] = ()

    @property
    def authority(self) -> dict[str, bool]:
        return {
            "grant_further_tool_access": False,
            "promote_memory": False,
            "approve_action": False,
            "mutate_governance": False,
            "widen_scope": False,
        }
