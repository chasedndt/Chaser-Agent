from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path

from chaser_agent.schemas import SourceInput

DESIGN_KEYWORDS = (
    "design",
    "contrast",
    "dark mode",
    "keywords",
    "keyword",
    "hierarchy",
    "readability",
    "user intent",
    "spacing",
    "restraint",
    "hero",
    "white",
    "overdecorated",
)

PROMOTION_WARNING = (
    "This artifact is review-only. It does not promote memory, mutate ChaseOS canonical truth, "
    "update the roadmap, create tasks, activate adapters, call providers, or prove production readiness. "
    "Canonical promotion requires ChaseOS governance."
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_run_id(input_path: Path, created_at: str) -> str:
    seed = f"{input_path.as_posix()}::{created_at}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()[:10]
    safe_stem = re.sub(r"[^a-z0-9]+", "-", input_path.stem.lower()).strip("-") or "source"
    timestamp = created_at.replace(":", "").replace("-", "").replace("Z", "z")
    return f"source-card-{timestamp}-{safe_stem}-{digest}"


def source_id_for_path(input_path: Path, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
    safe_stem = re.sub(r"[^a-z0-9]+", "-", input_path.stem.lower()).strip("-") or "source"
    return f"{safe_stem}-{digest}"


def title_for_path(input_path: Path) -> str:
    return input_path.stem.replace("_", " ").replace("-", " ").title()


def sentence_chunks(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    chunks = re.split(r"(?<=[.!?])\s+|\n+", normalized)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def source_summary(text: str) -> str:
    sentences = sentence_chunks(text)
    summary = " ".join(sentences[:3]).strip()
    if not summary:
        return "No source text provided."
    if len(summary) > 500:
        summary = summary[:497].rstrip() + "..."
    return summary


def _line_location(text: str, needle: str) -> str:
    lowered_needle = needle.lower()
    for index, line in enumerate(text.splitlines(), start=1):
        if lowered_needle and lowered_needle[:80] in line.lower():
            return f"line {index}"
    return "approximate source text"


def extract_claims(text: str, privacy_class: str) -> tuple[list[dict], list[dict]]:
    sentences = sentence_chunks(text)
    selected: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in DESIGN_KEYWORDS):
            selected.append(sentence)
    if not selected and sentences:
        selected = sentences[:3]

    claims = []
    evidence = []
    for index, sentence in enumerate(selected, start=1):
        claim_id = f"claim-{index:03d}"
        snippet_id = f"evidence-{index:03d}"
        location = _line_location(text, sentence)
        claim_type = "constraint" if any(word in sentence.lower() for word in ("should", "need", "can hurt", "must")) else "fact"
        claims.append(
            {
                "claim_id": claim_id,
                "claim_text": sentence,
                "evidence_snippet_id": snippet_id,
                "source_location": location,
                "claim_type": claim_type,
                "confidence": "high",
                "review_note": "Deterministically extracted from source text; human review still required.",
            }
        )
        evidence.append(
            {
                "snippet_id": snippet_id,
                "text": sentence,
                "source_location": location,
                "supports_claim_ids": [claim_id],
                "privacy_class": privacy_class,
                "redaction_note": None,
            }
        )
    return claims, evidence


def build_uncertainties(claim_ids: list[str]) -> list[dict]:
    return [
        {
            "uncertainty_id": "uncertainty-001",
            "label": "requires_review",
            "explanation": "This deterministic harness preserves source claims but does not judge design quality; human/design review is required.",
            "related_claim_ids": claim_ids,
        },
        {
            "uncertainty_id": "uncertainty-002",
            "label": "missing_context",
            "explanation": "The source does not include screenshots, metrics, user research, implementation details, or measured accessibility results.",
            "related_claim_ids": claim_ids,
        },
        {
            "uncertainty_id": "uncertainty-003",
            "label": "promotion_blocked",
            "explanation": "No source-card output may be promoted automatically to memory, tasks, roadmap, or ChaseOS canonical truth.",
            "related_claim_ids": claim_ids,
        },
    ]


def build_inferences(claim_ids: list[str]) -> list[dict]:
    return [
        {
            "inference_id": "inference-001",
            "inference_text": "A review packet for this source should check hierarchy, spacing, contrast, restraint, readability, subtle emphasis, and user intent before recommending design changes.",
            "based_on_claim_ids": claim_ids,
            "confidence": "medium",
            "uncertainty_label_ids": ["uncertainty-001", "uncertainty-002"],
        }
    ]


def build_action_candidates(claim_ids: list[str]) -> list[dict]:
    return [
        {
            "action_id": "action-001",
            "action_text": "Review the generated source card and decide whether this toy website-design scenario should become a future contract-eval seed.",
            "source_claim_ids": claim_ids,
            "rationale": "The source contains concrete review criteria but V0 may only propose review-only next steps.",
            "risk_level": "low",
            "requires_approval": True,
            "blocked_reason": None,
            "suggested_owner": "human_operator",
        },
        {
            "action_id": "action-002",
            "action_text": "If useful, compare future website-design outputs against source-grounded hierarchy, contrast, readability, restraint, and user-intent checks.",
            "source_claim_ids": claim_ids,
            "rationale": "This is a candidate review idea, not an executed redesign or roadmap mutation.",
            "risk_level": "low",
            "requires_approval": True,
            "blocked_reason": None,
            "suggested_owner": "human_operator",
        },
    ]


def build_memory_candidates(evidence: list[dict], privacy_class: str) -> list[dict]:
    first_evidence_id = evidence[0]["snippet_id"] if evidence else "evidence-000"
    return [
        {
            "memory_candidate_id": "memory-001",
            "candidate_text": "Chaser agent website-design review may need to preserve hierarchy, spacing, contrast, restraint, readability, subtle keyword emphasis, and user intent as review criteria.",
            "evidence_snippet_id": first_evidence_id,
            "scope": "workflow",
            "stability": "likely_stable",
            "privacy_class": privacy_class,
            "promotion_status": "candidate_only",
            "review_required": True,
            "rejection_reason": None,
        }
    ]


def build_source_card_artifacts(source: SourceInput, input_path: Path, run_id: str, created_at: str) -> dict[str, dict | list]:
    claims, evidence = extract_claims(source.text, source.privacy_class)
    claim_ids = [claim["claim_id"] for claim in claims]
    uncertainties = build_uncertainties(claim_ids)
    inferences = build_inferences(claim_ids)
    actions = build_action_candidates(claim_ids)
    memories = build_memory_candidates(evidence, source.privacy_class)
    contradictions: list[dict] = []

    source_card = {
        "source_id": source.id,
        "source_title": source.title,
        "source_type": source.source_type,
        "source_origin": source.source_origin,
        "privacy_class": source.privacy_class,
        "trust_state": "unreviewed",
        "source_summary": source_summary(source.text),
        "source_claims": claims,
        "chaser_agent_inferences": inferences,
        "uncertainty_labels": uncertainties,
        "contradiction_notes": contradictions,
        "action_candidates": actions,
        "memory_candidates": memories,
        "review_status": "pending_review",
        "promotion_status": "not_promoted",
        "created_at": created_at,
        "run_id": run_id,
    }

    human_review_packet = {
        "run_id": run_id,
        "source_id": source.id,
        "operator_review_status": "pending_review",
        "scores": {
            "source_fidelity": None,
            "inference_separation": None,
            "uncertainty_handling": None,
            "action_usefulness": None,
            "memory_safety": None,
        },
        "checklists": {
            "source_fidelity": ["pending: human must verify summary and claims are source-grounded"],
            "inference_separation": ["pending: human must verify inferences remain separate from source claims"],
            "uncertainty": ["pending: missing context and promotion boundaries are labeled"],
            "action_usefulness": ["pending: action candidates require approval and do not execute anything"],
            "memory_safety": ["pending: memory candidates are candidate_only and review_required"],
        },
        "canonical_promotion_warning": PROMOTION_WARNING,
        "pass_fail_decision": "needs_human_review",
        "reviewer_notes": "Pending human review. Deterministic harness output only.",
    }

    return {
        "source_card.json": source_card,
        "claims_table.json": {"run_id": run_id, "source_id": source.id, "claims": claims},
        "evidence_snippets.json": {"run_id": run_id, "source_id": source.id, "evidence_snippets": evidence},
        "uncertainty_labels.json": {"run_id": run_id, "source_id": source.id, "uncertainty_labels": uncertainties},
        "action_candidates.json": {"run_id": run_id, "source_id": source.id, "action_candidates": actions},
        "memory_candidates.json": {"run_id": run_id, "source_id": source.id, "memory_candidates": memories},
        "human_review_packet.json": human_review_packet,
    }


def source_input_from_file(input_path: Path, privacy_class: str = "public_toy") -> SourceInput:
    text = input_path.read_text(encoding="utf-8")
    return SourceInput(
        id=source_id_for_path(input_path, text),
        title=title_for_path(input_path),
        text=text,
        source_type="note" if input_path.suffix.lower() in {".md", ".txt"} else "other_safe_text",
        source_origin=f"local_file:{input_path.as_posix()}",
        privacy_class=privacy_class,
    )

# Backward-compatible placeholder API used by older smoke tests.
def build_source_card(source: SourceInput):
    from chaser_agent.schemas import Claim, SourceCard

    text = " ".join(source.text.split())
    first_sentence = text.split(".")[0].strip() if text else ""
    summary = first_sentence + ("." if first_sentence and not first_sentence.endswith(".") else "")
    if not summary:
        summary = "No source text provided."
    evidence = source.text[:240]
    claims = [Claim(text=summary, evidence=evidence, uncertainty="requires_review")]
    return SourceCard(
        source_id=source.id,
        title=source.title,
        summary=summary,
        claims=claims,
        memory_candidates=[],
        uncertainty_labels=["requires_review"],
    )
