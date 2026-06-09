from __future__ import annotations
from chaser_agent.schemas import SourceInput, SourceCard, Claim, MemoryCandidate


def build_source_card(source: SourceInput) -> SourceCard:
    """Build a deterministic placeholder source card without LLM calls.

    This compatibility wrapper preserves the original smoke-test API. The Phase 1
    harness lives in `chaser_agent.source_card` and writes full V0 artifacts.
    """
    text = " ".join(source.text.split())
    first_sentence = text.split(".")[0].strip() if text else ""
    summary = first_sentence + ("." if first_sentence and not first_sentence.endswith(".") else "")
    if not summary:
        summary = "No source text provided."
    evidence = source.text[:240]
    claims = [Claim(text=summary, evidence=evidence, uncertainty="requires_review")]
    memory_candidates = []
    lowered = source.text.lower()
    if "memory" in lowered or "remember" in lowered:
        memory_candidates.append(MemoryCandidate(text="Review whether this source contains a durable memory candidate.", evidence=evidence))
    return SourceCard(source_id=source.id, title=source.title, summary=summary, claims=claims, memory_candidates=memory_candidates, uncertainty_labels=["requires_review"])
