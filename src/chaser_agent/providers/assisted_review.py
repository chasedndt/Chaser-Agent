"""Run a source review with an injected provider adapter.

This is the model-assisted path. It never replaces the deterministic result: the
deterministic artifacts are built first and remain the baseline, and provider
output is appended only as quarantined candidates. If the provider fails,
refuses, or is over budget, the deterministic result still stands — degradation
is graceful by construction, not by error handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chaser_agent.providers.budget import BudgetExceeded, BudgetLedger, BudgetPolicy, enforce_deadline
from chaser_agent.providers.envelope import EnvelopeRefused, build_request
from chaser_agent.providers.quarantine import ProviderOutcome, apply_model_candidates, quarantine_response
from chaser_agent.run_artifacts import build_run_log
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts

DEFAULT_PROMPT_TEMPLATE = (
    "Read the source below and propose one additional inference a reviewer should consider. "
    "Do not assert approval, promotion, or completion.\n\nSOURCE:\n{source_text}"
)


def build_baseline_artifacts(
    source: SourceInput,
    run_id: str = "assisted-run",
    created_at: str = "1970-01-01T00:00:00Z",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    artifacts = build_source_card_artifacts(source, Path(f"{source.id}.md"), run_id, created_at)
    artifacts["run_log.json"] = build_run_log(
        run_id=run_id,
        created_at=created_at,
        command=f"assisted-review:{source.id}",
        input_source_id=source.id,
        output_paths=[Path("run_log.json")],
        repo_root=repo_root,
    )
    return artifacts


def run_assisted_review(
    source: SourceInput,
    adapter: Any,
    *,
    run_id: str = "assisted-run",
    created_at: str = "1970-01-01T00:00:00Z",
    policy: BudgetPolicy | None = None,
    ledger: BudgetLedger | None = None,
    prompt_template: str = DEFAULT_PROMPT_TEMPLATE,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return baseline artifacts, assisted artifacts, the outcome, and usage."""
    budget_policy = policy or BudgetPolicy()
    budget = ledger or BudgetLedger(policy=budget_policy)
    baseline = build_baseline_artifacts(source, run_id, created_at, repo_root)

    def degraded(reason: str) -> dict[str, Any]:
        """Provider unavailable or refused: the deterministic result stands."""
        outcome = ProviderOutcome(
            request_id="",
            provider_id=getattr(adapter, "provider_id", "unknown"),
            status="error",
            trust_state="untrusted_model_output",
            usable=False,
            candidate_text="",
            rejection_reasons=(reason,),
        )
        return {
            "baseline_artifacts": baseline,
            "assisted_artifacts": apply_model_candidates(baseline, outcome),
            "outcome": outcome,
            "usage": budget.totals(),
            "degraded": True,
        }

    try:
        request = build_request(
            purpose="inference_drafting",
            run_id=run_id,
            profile_id=str(source.source_type),
            privacy_class=source.privacy_class,
            prompt=prompt_template.format(source_text=source.text),
            created_at=created_at,
            max_output_tokens=budget_policy.max_output_tokens,
        )
        budget.check_before_send(request, getattr(adapter, "provider_id", "fake"))
    except (EnvelopeRefused, BudgetExceeded) as exc:
        return degraded(f"{type(exc).__name__}: {exc}")

    response = enforce_deadline(adapter.complete(request), budget_policy)
    budget.record(request, response)
    outcome = quarantine_response(response)

    return {
        "baseline_artifacts": baseline,
        "assisted_artifacts": apply_model_candidates(baseline, outcome),
        "outcome": outcome,
        "usage": budget.totals(),
        "degraded": False,
    }
