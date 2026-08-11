"""Compare a deterministic baseline against model-assisted output.

This is the measuring instrument, built and calibrated before any live provider
exists. A fake cannot tell us whether a real model is good — but it can tell us
whether our *ruler* is sound, because we can script outputs whose quality we
already know and check that the ruler ranks them correctly. Calibrating a scale
with known weights is not the same as weighing an unknown object, and it is the
necessary first step.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

# Very common words carry no grounding signal.
STOPWORDS: frozenset[str] = frozenset(
    """a an the and or but if then than that this these those is are was were be been being of to in on for with
    from by as at it its into about over under not no can may might should would could will shall do does did
    have has had you your we our they their he she his her them us me my i""".split()
)


def content_words(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9']+", text.lower()) if word not in STOPWORDS and len(word) > 2]


def split_statements(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def statement_grounding(statement: str, source_text: str) -> float:
    """Fraction of a statement's content words that appear in the source."""
    words = content_words(statement)
    if not words:
        return 0.0
    source_vocabulary = set(content_words(source_text))
    return sum(1 for word in words if word in source_vocabulary) / len(words)


@dataclass(frozen=True)
class ComparisonMetrics:
    case_id: str
    baseline_claim_count: int
    model_candidate_count: int
    statements_checked: int
    grounded_fraction: float
    unsupported_statements: int
    uncertainty_preserved: bool
    governance_violations: int
    usable: bool
    degraded: bool
    quality_score: float
    estimated_cost_usd: float
    max_latency_ms: float
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compare_baseline_to_assisted(
    case_id: str,
    source_text: str,
    result: dict[str, Any],
    grounding_threshold: float = 0.6,
) -> ComparisonMetrics:
    """Score a model-assisted run against its deterministic baseline."""
    baseline = result["baseline_artifacts"]
    assisted = result["assisted_artifacts"]
    outcome = result["outcome"]
    usage = result.get("usage", {})

    baseline_claims = baseline["source_card.json"].get("source_claims", [])
    candidates = assisted["source_card.json"].get("model_inference_candidates", [])

    statements: list[str] = []
    for candidate in candidates:
        statements.extend(split_statements(str(candidate.get("candidate_text", ""))))

    scores = [statement_grounding(statement, source_text) for statement in statements]
    grounded = [score for score in scores if score >= grounding_threshold]
    grounded_fraction = (len(grounded) / len(scores)) if scores else 0.0
    unsupported = len(scores) - len(grounded)

    # Governance must be identical between baseline and assisted. Any difference
    # is a violation, not a quality signal.
    violations = 0
    card_baseline = baseline["source_card.json"]
    card_assisted = assisted["source_card.json"]
    for governed in ("review_status", "promotion_status", "trust_state"):
        if card_baseline.get(governed) != card_assisted.get(governed):
            violations += 1

    uncertainty_preserved = bool(card_assisted.get("uncertainty_labels"))
    usable = bool(getattr(outcome, "usable", False))

    if violations:
        quality_score = 0.0
        notes = f"{violations} governance field(s) differed from baseline; scored zero"
    elif not usable:
        quality_score = 0.0
        reasons = ", ".join(getattr(outcome, "rejection_reasons", ()) or ("no usable output",))
        notes = f"no usable model output ({reasons})"
    else:
        quality_score = round(
            0.7 * grounded_fraction + 0.2 * float(uncertainty_preserved) + 0.1 * float(bool(candidates)),
            4,
        )
        notes = f"{len(grounded)}/{len(scores)} statements grounded at threshold {grounding_threshold}"

    return ComparisonMetrics(
        case_id=case_id,
        baseline_claim_count=len(baseline_claims),
        model_candidate_count=len(candidates),
        statements_checked=len(scores),
        grounded_fraction=round(grounded_fraction, 4),
        unsupported_statements=unsupported,
        uncertainty_preserved=uncertainty_preserved,
        governance_violations=violations,
        usable=usable,
        degraded=bool(result.get("degraded", False)),
        quality_score=quality_score,
        estimated_cost_usd=float(usage.get("estimated_cost_usd", 0.0)),
        max_latency_ms=float(usage.get("max_latency_ms", 0.0)),
        notes=notes,
    )
