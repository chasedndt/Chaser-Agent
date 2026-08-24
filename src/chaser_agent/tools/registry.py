"""Least-authority tool registry: default deny, explicit grant, scoped targets.

Three separate gates must all pass before a call is even authorized:

1. the tool is registered with a declared capability;
2. the tool has been explicitly granted for this run (registration is not
   permission - declaring a capability describes it, it does not enable it);
3. the concrete target falls inside the capability's declared scopes.

Authorization still does not execute anything. P0.1 plans calls and records that
it did not run them; `execute()` raises.
"""

from __future__ import annotations

import posixpath
from collections import Counter
from urllib.parse import unquote, urlparse

from chaser_agent.tools.models import (
    PERMITTED_SIDE_EFFECTS_P0_1,
    ToolCapability,
    ToolInvocationPlan,
    ToolRequest,
)


class ToolDenied(Exception):
    """Raised when a tool call falls outside its declared contract."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code
        self.message = message


def _is_url_scope(scope: str) -> bool:
    return scope.startswith(("http://", "https://"))


def _within_path_scope(target: str, scope: str) -> bool:
    """True only if target stays inside scope after normalisation.

    Normalising first is what stops `docs/../../etc/passwd` from passing a naive
    prefix check.
    """
    if target.startswith(("http://", "https://")) or posixpath.isabs(target):
        return False
    normalised = posixpath.normpath(target)
    if normalised.startswith("../") or normalised == "..":
        return False
    scope_normalised = posixpath.normpath(scope)
    return normalised == scope_normalised or normalised.startswith(scope_normalised.rstrip("/") + "/")


def _within_url_scope(target: str, scope: str) -> bool:
    target_parts = urlparse(target)
    scope_parts = urlparse(scope)
    if target_parts.scheme not in {"http", "https"} or scope_parts.scheme not in {"http", "https"}:
        return False
    if target_parts.scheme != scope_parts.scheme:
        return False
    if target_parts.username is not None or target_parts.password is not None:
        return False
    if scope_parts.username is not None or scope_parts.password is not None:
        return False
    if target_parts.hostname is None or target_parts.hostname != scope_parts.hostname:
        return False

    try:
        target_port = target_parts.port or (443 if target_parts.scheme == "https" else 80)
        scope_port = scope_parts.port or (443 if scope_parts.scheme == "https" else 80)
    except ValueError:
        return False
    if target_port != scope_port:
        return False

    def canonical_path(raw_path: str) -> str | None:
        decoded = raw_path or "/"
        for _ in range(4):
            next_decoded = unquote(decoded)
            if next_decoded == decoded:
                break
            decoded = next_decoded
        else:
            return None
        if "\\" in decoded or "\x00" in decoded:
            return None
        canonical = posixpath.normpath(decoded)
        return canonical if canonical.startswith("/") else f"/{canonical}"

    scope_path = canonical_path(scope_parts.path)
    target_path = canonical_path(target_parts.path)
    if scope_path is None or target_path is None:
        return False
    if scope_path == "/":
        return True
    scope_root = scope_path.rstrip("/")
    return target_path == scope_root or target_path.startswith(scope_root + "/")


def target_within_scopes(target: str, scopes: tuple[str, ...]) -> bool:
    for scope in scopes:
        if _is_url_scope(scope):
            if _within_url_scope(target, scope):
                return True
        elif _within_path_scope(target, scope):
            return True
    return False


class ToolRegistry:
    """Declared capabilities plus per-run grants. Registration is not permission."""

    def __init__(self) -> None:
        self._capabilities: dict[str, ToolCapability] = {}
        self._granted: set[str] = set()
        self._call_counts: Counter[str] = Counter()

    # --- declaration ---------------------------------------------------------

    def register(self, capability: ToolCapability) -> None:
        if capability.tool_id in self._capabilities:
            raise ValueError(f"tool already registered: {capability.tool_id}")
        self._capabilities[capability.tool_id] = capability

    def capability(self, tool_id: str) -> ToolCapability | None:
        return self._capabilities.get(tool_id)

    @property
    def registered_tool_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._capabilities))

    # --- granting ------------------------------------------------------------

    def grant(self, tool_id: str) -> None:
        """Explicitly enable a registered tool for this run."""
        if tool_id not in self._capabilities:
            raise ToolDenied("unregistered_tool", f"cannot grant unknown tool {tool_id!r}")
        self._granted.add(tool_id)

    def revoke(self, tool_id: str) -> None:
        self._granted.discard(tool_id)

    @property
    def granted_tool_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._granted))

    # --- authorization -------------------------------------------------------

    def authorize(self, request: ToolRequest) -> ToolCapability:
        capability = self._capabilities.get(request.tool_id)
        if capability is None:
            raise ToolDenied("unregistered_tool", f"{request.tool_id!r} has no declared capability")
        if request.tool_id not in self._granted:
            raise ToolDenied("tool_not_granted", f"{request.tool_id!r} is registered but not granted for this run")
        if capability.side_effect_class not in PERMITTED_SIDE_EFFECTS_P0_1:
            raise ToolDenied(
                "side_effect_not_permitted",
                f"{capability.side_effect_class!r} calls are not permitted in P0.1",
            )
        if not target_within_scopes(request.target, capability.allowed_scopes):
            raise ToolDenied(
                "scope_violation",
                f"target {request.target!r} is outside declared scopes {capability.allowed_scopes}",
            )
        if self._call_counts[request.tool_id] >= capability.max_calls_per_run:
            raise ToolDenied(
                "call_budget_exceeded",
                f"{request.tool_id!r} already used its {capability.max_calls_per_run} call budget",
            )
        return capability

    def plan(self, request: ToolRequest) -> ToolInvocationPlan:
        """Authorize a call and record that it was deliberately not executed."""
        try:
            capability = self.authorize(request)
        except ToolDenied as denial:
            return ToolInvocationPlan(
                request_hash=request.request_hash,
                tool_id=request.tool_id,
                target=request.target,
                side_effect_class=(
                    self._capabilities[request.tool_id].side_effect_class
                    if request.tool_id in self._capabilities
                    else "read_only"
                ),
                authorized=False,
                denial_reason=denial.reason_code,
            )
        self._call_counts[request.tool_id] += 1
        return ToolInvocationPlan(
            request_hash=request.request_hash,
            tool_id=request.tool_id,
            target=request.target,
            side_effect_class=capability.side_effect_class,
            authorized=True,
        )

    def execute(self, request: ToolRequest) -> None:
        raise ToolDenied("execution_not_implemented", "tool execution is not available in P0.1")
