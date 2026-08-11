"""Calibrate the deterministic-vs-model comparison ruler.

A fake cannot tell us whether a real model is good. It can tell us whether our
measuring instrument is sound: we script outputs whose quality we already know
(well-grounded, partly grounded, wholly fabricated) and require the ruler to
rank them in that order. Calibrating a scale with known weights is not weighing
an unknown object — but an uncalibrated scale makes the later weighing
meaningless.
"""

from __future__ import annotations

import pytest

from chaser_agent.evals.comparison import (
    compare_baseline_to_assisted,
    content_words,
    split_statements,
    statement_grounding,
)
from chaser_agent.providers.assisted_review import run_assisted_review
from chaser_agent.providers.fake import FakeProviderAdapter, ScriptedReply
from chaser_agent.schemas import SourceInput

SOURCE_TEXT = (
    "A review packet is not an approval. Memory candidates require human review before promotion. "
    "Evidence snippets must remain linked to the claims they support."
)
SOURCE = SourceInput(
    id="comparison-case", title="Comparison Case", text=SOURCE_TEXT, privacy_class="public_toy"
)

GROUNDED = (
    "The review packet remains distinct from approval. "
    "Memory candidates still require human review before promotion."
)
PARTIAL = (
    "Memory candidates require human review before promotion. "
    "The quarterly revenue forecast suggests hiring twelve additional sales engineers."
)
FABRICATED = (
    "The quarterly revenue forecast suggests hiring twelve additional sales engineers. "
    "Kubernetes autoscaling reduced our Redis eviction rate substantially last winter."
)


def score_for(text: str) -> float:
    adapter = FakeProviderAdapter(ScriptedReply.ok(text))
    result = run_assisted_review(SOURCE, adapter)
    return compare_baseline_to_assisted("comparison-case", SOURCE_TEXT, result).quality_score


# --- grounding primitives ----------------------------------------------------------


def test_content_words_drop_stopwords():
    assert "review" in content_words("A review of the packet")
    assert "the" not in content_words("A review of the packet")


def test_split_statements_separates_sentences():
    assert len(split_statements("One claim. Two claims! Three?")) == 3


def test_statement_grounding_is_high_for_source_text_and_low_for_invention():
    grounded = statement_grounding("Memory candidates require human review before promotion.", SOURCE_TEXT)
    invented = statement_grounding("Kubernetes autoscaling reduced Redis eviction rates.", SOURCE_TEXT)
    assert grounded > 0.8
    assert invented < 0.2


def test_empty_statement_scores_zero():
    assert statement_grounding("", SOURCE_TEXT) == 0.0


# --- the calibration: known weights, correct ordering -------------------------------


def test_ruler_ranks_known_quality_outputs_in_the_correct_order():
    grounded_score = score_for(GROUNDED)
    partial_score = score_for(PARTIAL)
    fabricated_score = score_for(FABRICATED)

    assert grounded_score > partial_score > fabricated_score, (
        f"ruler mis-ranked known outputs: grounded={grounded_score}, "
        f"partial={partial_score}, fabricated={fabricated_score}"
    )


def test_fabricated_output_is_reported_as_unsupported():
    adapter = FakeProviderAdapter(ScriptedReply.ok(FABRICATED))
    metrics = compare_baseline_to_assisted(
        "comparison-case", SOURCE_TEXT, run_assisted_review(SOURCE, adapter)
    )

    assert metrics.unsupported_statements >= 2
    assert metrics.grounded_fraction < 0.5


def test_grounded_output_is_reported_as_supported():
    adapter = FakeProviderAdapter(ScriptedReply.ok(GROUNDED))
    metrics = compare_baseline_to_assisted(
        "comparison-case", SOURCE_TEXT, run_assisted_review(SOURCE, adapter)
    )

    assert metrics.grounded_fraction == 1.0
    assert metrics.unsupported_statements == 0
    assert metrics.governance_violations == 0
    assert metrics.uncertainty_preserved is True


# --- the ruler cannot be gamed by authority claims ----------------------------------


@pytest.mark.parametrize("payload_name", ["forged_promotion", "instruction_injection", "fabricated_certainty"])
def test_hostile_output_scores_zero_regardless_of_wording(payload_name: str):
    adapter = FakeProviderAdapter(ScriptedReply.hostile(payload_name))
    metrics = compare_baseline_to_assisted(
        "comparison-case", SOURCE_TEXT, run_assisted_review(SOURCE, adapter)
    )

    assert metrics.quality_score == 0.0
    assert metrics.usable is False


def test_failed_provider_scores_zero_and_is_marked_not_a_quality_signal():
    adapter = FakeProviderAdapter(ScriptedReply.timeout())
    metrics = compare_baseline_to_assisted(
        "comparison-case", SOURCE_TEXT, run_assisted_review(SOURCE, adapter)
    )

    assert metrics.quality_score == 0.0
    assert metrics.usable is False
    assert "no usable model output" in metrics.notes


def test_metrics_carry_baseline_context_and_usage():
    adapter = FakeProviderAdapter(ScriptedReply.ok(GROUNDED))
    metrics = compare_baseline_to_assisted(
        "comparison-case", SOURCE_TEXT, run_assisted_review(SOURCE, adapter)
    )

    assert metrics.baseline_claim_count > 0
    assert metrics.model_candidate_count == 1
    assert metrics.estimated_cost_usd == 0.0
    assert metrics.to_dict()["case_id"] == "comparison-case"
