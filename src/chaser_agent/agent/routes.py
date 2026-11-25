"""Which route answers a job, and why. A small deterministic guard, never the model.

Every reasoner belongs to one route kind. The ladder tries them in this order:

1. ``plan``: the person's own plan sign-in (ChatGPT through Codex, a Claude plan, any
   provider that lets a person sign in), run by that provider's own program on this
   computer. Only for the person's own work.
2. ``api_key``: the person's own API key for any provider. ``local`` models on this
   computer sit in the same tier: nobody else's terms are involved.
3. ``cloud``: ChaseOS Cloud, the route that never stops. It takes over when a plan's
   limits run out or when the guard refuses a plan for the job.

The guard:

- own work on the person's own computer: a plan is allowed;
- work for a client, or anything sold: an API key, a local model or Cloud only;
- a Claude plan: interactive use only, never a headless job.

A plan sign-in stays with the provider's own program on the person's computer. Nothing
here reads, copies or sends it: a plan route is refused on a hosted machine, and the
receipt names the route, never a credential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

PLAN = "plan"
API_KEY = "api_key"
LOCAL = "local"
CLOUD = "cloud"
BRIDGE = "bridge"
TEST = "test"
UNKNOWN = "unknown"

# Lower tiers are tried first. A fallback only ever moves to a later tier.
TIERS = {PLAN: 0, API_KEY: 1, LOCAL: 1, CLOUD: 2}
WORK_FOR = ("owner", "client", "sale")
MACHINES = ("own", "hosted")
# A route that stops for one of these has run out of allowance, not broken: the next tier takes the job.
LIMIT_CODES = frozenset({"plan_limit", "out_of_credits", "rate_limited"})


@dataclass(frozen=True)
class Job:
    """Who the work is for and how it runs. Set by the caller and the workflow, never by the model."""

    work_for: str = "owner"
    interactive: bool = False
    machine: str = "own"

    def __post_init__(self) -> None:
        if self.work_for not in WORK_FOR:
            raise ValueError(f"work_for must be one of {', '.join(WORK_FOR)}")
        if self.machine not in MACHINES:
            raise ValueError(f"machine must be one of {', '.join(MACHINES)}")
        if not isinstance(self.interactive, bool):
            raise ValueError("interactive must be true or false")

    @classmethod
    def from_request(cls, value: Any, *, machine: str = "own", workflow_work_for: str | None = None) -> "Job":
        """A caller's job fields. The machine comes from the service, and a workflow can only raise who the work is for."""
        value = value or {}
        if not isinstance(value, dict) or set(value) - {"work_for", "interactive"}:
            raise ValueError("job takes only work_for and interactive")
        work_for = value.get("work_for", "owner")
        if workflow_work_for and work_for == "owner":
            work_for = workflow_work_for
        return cls(work_for=work_for, interactive=value.get("interactive", False), machine=machine)

    def as_record(self) -> dict[str, Any]:
        return {"work_for": self.work_for, "interactive": self.interactive, "machine": self.machine}


@dataclass(frozen=True)
class RouteInfo:
    reasoner_id: str
    label: str
    kind: str
    provider: str

    @property
    def tier(self) -> int:
        return TIERS.get(self.kind, 0)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    explanation: str


def route_info(reasoner: Any) -> RouteInfo:
    """A reasoner names its route kind and provider. One that doesn't is treated as a personal sign-in, the strictest case."""
    kind = getattr(reasoner, "route_kind", UNKNOWN)
    provider = getattr(reasoner, "provider", "unknown")
    describe = getattr(reasoner, "route_details", None)
    if callable(describe):
        try:
            details = describe() or {}
            kind = details.get("kind", kind)
            provider = details.get("provider", provider)
        except Exception:  # A broken description must not widen what the route may do.
            kind = UNKNOWN
    return RouteInfo(reasoner.reasoner_id, getattr(reasoner, "label", reasoner.reasoner_id), str(kind), str(provider))


def check(job: Job, route: RouteInfo) -> Decision:
    """May this route answer this job? The reason code goes on the receipt."""
    if route.kind in (PLAN, UNKNOWN):
        personal = "A personal plan sign-in" if route.kind == PLAN else f"{route.label}, whose sign-in isn't declared,"
        if job.machine != "own":
            return Decision(False, "plan_needs_own_machine", f"{personal} stays on the person's own computer, and this service is hosted.")
        if job.work_for != "owner":
            return Decision(False, "plan_not_for_client_work", f"{personal} is for the person's own work. Work for a client or anything sold runs on an API key or ChaseOS Cloud.")
        if route.kind == PLAN and route.provider == "anthropic" and not job.interactive:
            return Decision(False, "claude_plan_interactive_only", "A Claude plan is for interactive use only, never a headless job.")
        return Decision(True, "own_plan_own_work", "The person's own plan, for their own work, on their own computer.")
    if route.kind == API_KEY:
        return Decision(True, "own_api_key", "The person's own API key, allowed for any job.")
    if route.kind == LOCAL:
        return Decision(True, "local_model", "A model running on this computer, allowed for any job.")
    if route.kind == CLOUD:
        return Decision(True, "chaseos_cloud", "ChaseOS Cloud on the owner's key, allowed for any job.")
    if route.kind == BRIDGE:
        if job.work_for != "owner":
            return Decision(False, "bridge_owner_only", "Another harness answering over the local API uses its own sign-in, so it takes only the owner's work.")
        return Decision(True, "bridge_owner_work", "Another harness on this computer, for the owner's own work.")
    if route.kind == TEST:
        return Decision(True, "test_route", "Scripted test replies.")
    return Decision(False, "unknown_route", f"{route.label} has an unrecognised route kind.")


@dataclass
class Choice:
    """The route picked for a job, and what was passed over on the way."""

    reasoner: Any
    route: RouteInfo
    decision: Decision
    job: Job
    passed_over: list[dict[str, Any]] = field(default_factory=list)
    fallback_from: dict[str, Any] | None = None

    def as_record(self) -> dict[str, Any]:
        record = {
            "reasoner": self.route.reasoner_id, "kind": self.route.kind, "provider": self.route.provider,
            "model": getattr(self.reasoner, "model", None), "reason": self.decision.reason,
            "explanation": self.decision.explanation, "job": self.job.as_record(), "passed_over": list(self.passed_over),
        }
        if self.fallback_from:
            record["fallback_from"] = self.fallback_from
        return record


class NoRoute(RuntimeError):
    def __init__(self, code: str, message: str, passed_over: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.passed_over = passed_over


def ladder(reasoners: Iterable[Any], *, preferred: str | None = None) -> list[Any]:
    """Every reasoner in ladder order: the preferred one first, then by tier, keeping registration order within a tier.

    The bridge isn't a rung: it answers only when asked for by name, or as a last resort while something is answering it."""
    rows = [r for r in reasoners if route_info(r).kind != BRIDGE]
    rows.sort(key=lambda r: route_info(r).tier)
    if preferred:
        rows.sort(key=lambda r: r.reasoner_id != preferred)
    return rows


def _status(reasoner: Any) -> dict[str, Any]:
    try:
        return reasoner.status() or {}
    except Exception as exc:  # A broken route must not stop the pick.
        return {"available": False, "reason": type(exc).__name__}


def choose(reasoners: dict[str, Any], job: Job, *, requested: str = "auto", preferred: str | None = None,
           after_tier: int | None = None, exclude: frozenset[str] = frozenset()) -> Choice:
    """The first route the guard allows and that is ready, in ladder order.

    ``requested`` names one route: it must pass the guard, and a refusal is final (the person asked for that route).
    ``after_tier`` keeps only later tiers, for a fallback after a route ran out of allowance."""
    passed: list[dict[str, Any]] = []
    if requested != "auto" and after_tier is None:
        reasoner = reasoners[requested]
        route = route_info(reasoner)
        decision = check(job, route)
        if not decision.allowed:
            raise NoRoute(decision.reason, decision.explanation, [{"reasoner": route.reasoner_id, "reason": decision.reason}])
        return Choice(reasoner, route, decision, job)
    for reasoner in ladder(reasoners.values(), preferred=preferred if after_tier is None else None):
        route = route_info(reasoner)
        if reasoner.reasoner_id in exclude or (after_tier is not None and route.tier <= after_tier):
            continue
        decision = check(job, route)
        if not decision.allowed:
            passed.append({"reasoner": route.reasoner_id, "kind": route.kind, "reason": decision.reason})
            continue
        state = _status(reasoner)
        if not state.get("available"):
            passed.append({"reasoner": route.reasoner_id, "kind": route.kind, "reason": "not_ready", "detail": str(state.get("reason") or "")[:200]})
            continue
        return Choice(reasoner, route, decision, job, passed)
    bridge = reasoners.get("bridge")
    if bridge is not None and after_tier is None and _status(bridge).get("connected"):
        route = route_info(bridge)
        decision = check(job, route)
        if decision.allowed:
            return Choice(bridge, route, decision, job, passed)
        passed.append({"reasoner": route.reasoner_id, "kind": route.kind, "reason": decision.reason})
    detail = " | ".join(f"{row['reasoner']}: {row.get('detail') or row['reason']}" for row in passed)
    raise NoRoute("no_route", "No AI model is connected, so this can't start. " + detail, passed)


def reply_cost(route: RouteInfo, reply: Any) -> dict[str, Any]:
    """What one reply cost, as far as the route reports it. Nothing is estimated or invented."""
    usage = getattr(reply, "usage", None) or {}
    tokens = {key: usage.get(key) for key in ("prompt_tokens", "completion_tokens") if usage.get(key) is not None}
    if route.kind == CLOUD:
        return {"basis": "chaseos_credits", "credits": getattr(reply, "credits", None), **tokens}
    if route.kind == API_KEY:
        return {"basis": "provider_tokens", "billed_by": route.provider, **tokens}
    if route.kind in (PLAN, UNKNOWN):
        return {"basis": "plan_allowance", "billed_by": route.provider}
    if route.kind == LOCAL:
        return {"basis": "local_compute"}
    return {"basis": "none"}


def add_cost(total: dict[str, Any] | None, cost: dict[str, Any]) -> dict[str, Any]:
    """A turn's running cost: credits and tokens add up; each basis seen is listed."""
    total = dict(total or {"credits": 0, "prompt_tokens": 0, "completion_tokens": 0, "bases": []})
    for key in ("credits", "prompt_tokens", "completion_tokens"):
        if isinstance(cost.get(key), int):
            total[key] = total.get(key, 0) + cost[key]
    if cost.get("basis") not in total["bases"]:
        total["bases"] = [*total["bases"], cost.get("basis")]
    return total
