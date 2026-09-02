"""Cost, token, and latency accounting for the provider boundary.

A fake cannot tell us a real provider's price or speed. It can, however, let us
build and prove the machinery that *bounds* them: a request refused before it is
sent when it would breach a ceiling, a deadline enforced by the harness rather
than trusted to the provider, and a per-run ledger that already exists when the
first live adapter arrives.

The residual unknown is therefore narrowed from "we have no cost control" to
"we do not yet know the real numbers".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from chaser_agent.providers.models import ProviderRequest, ProviderResponse

# Rough token estimate: ~4 characters per token. Deliberately an estimate, and
# labelled as one everywhere it is reported. A live adapter should replace this
# with provider-reported usage.
CHARACTERS_PER_TOKEN = 4

# Price per 1,000 tokens in USD, keyed by provider_id. The fake is free; real
# entries are added only when a provider is approved.
DEFAULT_PRICE_TABLE: dict[str, tuple[float, float]] = {"fake": (0.0, 0.0)}


class BudgetExceeded(Exception):
    """Raised before sending when a request would breach a declared ceiling."""


@dataclass(frozen=True)
class BudgetPolicy:
    max_prompt_characters: int = 20_000
    max_output_tokens: int = 1_024
    deadline_seconds: float = 30.0
    max_requests_per_run: int = 20
    max_estimated_cost_usd: float = 0.10


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + CHARACTERS_PER_TOKEN - 1) // CHARACTERS_PER_TOKEN) if text else 0


def estimate_cost_usd(
    provider_id: str,
    prompt_tokens: int,
    output_tokens: int,
    price_table: dict[str, tuple[float, float]] | None = None,
) -> float:
    table = price_table if price_table is not None else DEFAULT_PRICE_TABLE
    prompt_price, output_price = table.get(provider_id, (0.0, 0.0))
    return round((prompt_tokens / 1000) * prompt_price + (output_tokens / 1000) * output_price, 6)


@dataclass(frozen=True)
class UsageRecord:
    request_id: str
    provider_id: str
    status: str
    prompt_tokens: int
    output_tokens: int
    latency_ms: float
    estimated_cost_usd: float
    deadline_exceeded: bool = False


@dataclass
class BudgetLedger:
    """Enforces ceilings before sending and records what each call consumed."""

    policy: BudgetPolicy = field(default_factory=BudgetPolicy)
    price_table: dict[str, tuple[float, float]] = field(default_factory=lambda: dict(DEFAULT_PRICE_TABLE))
    records: list[UsageRecord] = field(default_factory=list)

    # --- pre-send ceilings ---------------------------------------------------

    def check_before_send(self, request: ProviderRequest, provider_id: str = "fake") -> None:
        if len(request.prompt) > self.policy.max_prompt_characters:
            raise BudgetExceeded(
                f"prompt of {len(request.prompt)} characters exceeds the "
                f"{self.policy.max_prompt_characters} character ceiling"
            )
        if request.max_output_tokens > self.policy.max_output_tokens:
            raise BudgetExceeded(
                f"max_output_tokens {request.max_output_tokens} exceeds the "
                f"{self.policy.max_output_tokens} ceiling"
            )
        if len(self.records) >= self.policy.max_requests_per_run:
            raise BudgetExceeded(
                f"run already made {len(self.records)} requests; ceiling is {self.policy.max_requests_per_run}"
            )
        projected = self.total_estimated_cost_usd() + estimate_cost_usd(
            provider_id, estimate_tokens(request.prompt), request.max_output_tokens, self.price_table
        )
        if projected > self.policy.max_estimated_cost_usd:
            raise BudgetExceeded(
                f"projected run cost ${projected:.6f} exceeds the ${self.policy.max_estimated_cost_usd:.6f} ceiling"
            )

    # --- post-send accounting ------------------------------------------------

    def record(self, request: ProviderRequest, response: ProviderResponse) -> UsageRecord:
        prompt_tokens = response.prompt_tokens or estimate_tokens(request.prompt)
        output_tokens = response.output_tokens or estimate_tokens(response.text)
        usage = UsageRecord(
            request_id=response.request_id,
            provider_id=response.provider_id,
            status=response.status,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            latency_ms=response.latency_ms,
            estimated_cost_usd=estimate_cost_usd(
                response.provider_id, prompt_tokens, output_tokens, self.price_table
            ),
            deadline_exceeded=response.latency_ms > self.policy.deadline_seconds * 1000,
        )
        self.records.append(usage)
        return usage

    def total_estimated_cost_usd(self) -> float:
        return round(sum(record.estimated_cost_usd for record in self.records), 6)

    def totals(self) -> dict[str, Any]:
        return {
            "requests": len(self.records),
            "prompt_tokens_estimated": sum(record.prompt_tokens for record in self.records),
            "output_tokens_estimated": sum(record.output_tokens for record in self.records),
            "estimated_cost_usd": self.total_estimated_cost_usd(),
            "max_latency_ms": max((record.latency_ms for record in self.records), default=0.0),
            "deadline_breaches": sum(1 for record in self.records if record.deadline_exceeded),
            "token_counts_are_estimates": True,
            "policy": {
                "max_prompt_characters": self.policy.max_prompt_characters,
                "max_output_tokens": self.policy.max_output_tokens,
                "deadline_seconds": self.policy.deadline_seconds,
                "max_requests_per_run": self.policy.max_requests_per_run,
                "max_estimated_cost_usd": self.policy.max_estimated_cost_usd,
            },
        }


def enforce_deadline(response: ProviderResponse, policy: BudgetPolicy) -> ProviderResponse:
    """Convert an over-deadline reply into a timeout.

    The harness decides what "too slow" means. A provider that answers late is
    not treated as a success just because bytes eventually arrived.
    """
    if response.latency_ms <= policy.deadline_seconds * 1000:
        return response
    return ProviderResponse(
        request_id=response.request_id,
        provider_id=response.provider_id,
        status="timeout",
        text="",
        error=(
            f"response took {response.latency_ms:.0f}ms, exceeding the "
            f"{policy.deadline_seconds * 1000:.0f}ms deadline"
        ),
        is_fake=response.is_fake,
        network_call_performed=response.network_call_performed,
        prompt_tokens=response.prompt_tokens,
        output_tokens=response.output_tokens,
        latency_ms=response.latency_ms,
    )
