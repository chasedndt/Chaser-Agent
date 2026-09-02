"""Document metadata must not be extracted as substantive source claims.

Found during operator review of a real run: on a research thesis, four of eight
extracted claims were the document's own metadata header (URL, Title, Published,
Authors) rather than anything the source asserted. The redesign required
heading-safe extraction; metadata header lines are the same defect in a
different shape.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chaser_agent.source_card import (
    build_source_card_artifacts,
    extract_claims,
    extract_source_metadata,
    sentence_chunks,
)
from chaser_agent.schemas import SourceInput

RESEARCH_NOTE = """# Monetization Gateway Thesis

## Source inspected

- URL: https://blog.cloudflare.com/monetization-gateway/
- Title: Announcing the Monetization Gateway
- Published: 2026-07-01
- Authors: Rohin Lohe, Justin Ridgely, Will Papper

## Findings

The gateway charges for any resource behind a proxy. Operators must review
pricing before enabling it.
"""


def claim_texts(text: str) -> list[str]:
    claims, _ = extract_claims(text, "public_toy")
    return [claim["claim_text"] for claim in claims]


@pytest.mark.parametrize("label", ["URL:", "Title:", "Published:", "Authors:"])
def test_metadata_lines_are_not_extracted_as_claims(label: str):
    for claim in claim_texts(RESEARCH_NOTE):
        assert not claim.startswith(label), f"metadata line extracted as a claim: {claim!r}"


def test_metadata_is_preserved_rather_than_discarded():
    metadata = extract_source_metadata(RESEARCH_NOTE)

    assert metadata["url"] == "https://blog.cloudflare.com/monetization-gateway/"
    assert metadata["title"] == "Announcing the Monetization Gateway"
    assert metadata["published"] == "2026-07-01"
    assert metadata["authors"] == "Rohin Lohe, Justin Ridgely, Will Papper"


def test_substantive_sentences_survive_metadata_filtering():
    claims = claim_texts(RESEARCH_NOTE)

    assert any("charges for any resource" in claim for claim in claims)
    assert any("review" in claim and "pricing" in claim for claim in claims)


def test_labelled_statements_that_are_real_claims_are_not_filtered():
    """Guard against over-filtering: not every 'Label: value' line is metadata."""
    text = (
        "Decision: we will use the deterministic harness as the baseline.\n"
        "Risk: the extractor may drop substantive lines.\n"
        "Note: reviewers need the provenance trail.\n"
    )
    claims = claim_texts(text)

    assert any(claim.startswith("Decision:") for claim in claims)
    assert any(claim.startswith("Risk:") for claim in claims)
    assert any(claim.startswith("Note:") for claim in claims)


def test_bare_url_line_is_not_a_claim():
    assert "https://example.com/post" not in " ".join(sentence_chunks("https://example.com/post\nA real sentence here.\n"))


def test_source_card_exposes_metadata_separately_from_claims():
    source = SourceInput(
        id="metadata-case", title="Metadata Case", text=RESEARCH_NOTE, privacy_class="public_toy"
    )
    artifacts = build_source_card_artifacts(source, Path("metadata-case.md"), "run-md", "1970-01-01T00:00:00Z")
    card = artifacts["source_card.json"]

    assert card["source_metadata"]["published"] == "2026-07-01"
    for claim in card["source_claims"]:
        assert not claim["claim_text"].lower().startswith(("url:", "title:", "published:", "authors:"))
