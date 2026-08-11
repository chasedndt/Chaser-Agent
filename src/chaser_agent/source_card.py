"""Canonical deterministic source-review builder.

Domain-specific review behaviour lives in explicit workflow profiles. This module
owns source parsing, evidence linkage, artifact assembly, and authority stamps.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from chaser_agent.core.protocols import WorkflowProfile
from chaser_agent.schemas import Claim, SourceCard, SourceInput
from chaser_agent.workflows import get_profile


PROMOTION_WARNING = (
    "This artifact is review-only. It does not promote memory, modify approved durable local state, "
    "mutate ChaseOS canonical truth, update a roadmap, create tasks, activate adapters, call providers, "
    "or prove production readiness. Promotion requires an explicit governance decision."
)

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+")
_LIST_PREFIX = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


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
    """Return content sentences without treating Markdown headings as claims."""
    chunks: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _HEADING.match(line):
            continue
        line = _LIST_PREFIX.sub("", line).strip()
        if line.startswith(">"):
            line = line[1:].strip()
        if not line:
            continue
        chunks.extend(part.strip() for part in _SENTENCE_BOUNDARY.split(line) if part.strip())
    return chunks


def source_summary(text: str) -> str:
    summary = " ".join(sentence_chunks(text)[:3]).strip()
    if not summary:
        return "No source text provided."
    return summary if len(summary) <= 500 else summary[:497].rstrip() + "..."


def _line_location(text: str, needle: str) -> str:
    lowered_needle = needle.lower()
    for index, line in enumerate(text.splitlines(), start=1):
        if lowered_needle and lowered_needle[:80] in line.lower():
            return f"line {index}"
    return "approximate source text"


def classify_claim_type(sentence: str) -> str:
    """Classify how the source presents a statement, never its global truth."""
    lowered = sentence.lower()
    if any(marker in lowered for marker in ("reported", "the study found", "results show", "outperformed", "measured")):
        return "reported_result"
    if any(marker in lowered for marker in ("must", "should", "needs", "need to", "required", "requirement")):
        return "requirement"
    if any(marker in lowered for marker in ("recommend", "best practice", "favours", "prefer")):
        return "recommendation"
    if any(marker in lowered for marker in ("is defined as", "means", "refers to", "definition")):
        return "definition"
    if any(marker in lowered for marker in ("we decided", "decision:", "will use", "chosen")):
        return "decision"
    if any(marker in lowered for marker in ("i think", "we think", "believe", "in my view", "opinion")):
        return "opinion"
    if any(marker in lowered for marker in ("cannot", "can't", "may not", "only", "limited to", "without")):
        return "constraint"
    return "unknown"


def extract_claims(text: str, privacy_class: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentence_chunks(text)[:8], start=1):
        claim_id = f"claim-{index:03d}"
        snippet_id = f"evidence-{index:03d}"
        location = _line_location(text, sentence)
        claims.append(
            {
                "claim_id": claim_id,
                "claim_text": sentence,
                "evidence_snippet_id": snippet_id,
                "source_location": location,
                "claim_type": classify_claim_type(sentence),
                "confidence": "high",
                "review_note": "Verbatim deterministic extraction; the confidence describes extraction, not source truth.",
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


def contradiction_notes() -> list[dict[str, Any]]:
    return [
        {
            "status": "not_evaluated",
            "explanation": "No profile rule requested a reliable deterministic contradiction check.",
            "related_claim_ids": [],
        }
    ]


def build_source_card_artifacts(
    source: SourceInput,
    input_path: Path,
    run_id: str,
    created_at: str,
    profile_id: str = "general_source_review",
) -> dict[str, dict[str, Any]]:
    profile: WorkflowProfile = get_profile(profile_id)
    if source.source_type not in profile.allowed_input_types:
        allowed = ", ".join(profile.allowed_input_types)
        raise ValueError(f"profile {profile.profile_id} does not allow input type {source.source_type!r}; allowed: {allowed}")

    claims, evidence = extract_claims(source.text, source.privacy_class)
    claim_ids = [claim["claim_id"] for claim in claims]
    uncertainties = profile.build_uncertainties(claim_ids, source.text)
    inferences = profile.build_inferences(claim_ids, source.text)
    actions = profile.build_actions(claim_ids, source.text)
    memories = profile.build_memories(claims, evidence, source.privacy_class)
    contradictions = contradiction_notes()

    source_card = {
        "source_id": source.id,
        "source_title": source.title,
        "source_type": source.source_type,
        "source_origin": source.source_origin,
        "privacy_class": source.privacy_class,
        "workflow_profile": profile.profile_id,
        "workflow_profile_version": profile.version,
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
        "workflow_profile": profile.profile_id,
        "required_review_dimensions": list(profile.required_review_dimensions),
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
            "uncertainty": ["pending: human must verify missing context and promotion boundaries"],
            "action_usefulness": ["pending: action candidates require approval and execute nothing"],
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


def build_source_card(source: SourceInput, profile_id: str = "general_source_review") -> SourceCard:
    """Compatibility API backed by the canonical artifact builder."""
    artifacts = build_source_card_artifacts(
        source,
        Path(f"{source.id}.txt"),
        run_id=f"compat-{source.id}",
        created_at="1970-01-01T00:00:00Z",
        profile_id=profile_id,
    )
    artifact = artifacts["source_card.json"]
    claims = [
        Claim(
            text=row["claim_text"],
            evidence=row["claim_text"],
            uncertainty="requires_review",
        )
        for row in artifact["source_claims"]
    ]
    from chaser_agent.schemas import MemoryCandidate

    memories = [
        MemoryCandidate(
            text=row["candidate_text"],
            evidence=row["evidence_snippet_id"],
            state="candidate",
        )
        for row in artifact["memory_candidates"]
    ]
    return SourceCard(
        source_id=source.id,
        title=source.title,
        summary=artifact["source_summary"],
        claims=claims,
        memory_candidates=memories,
        uncertainty_labels=[row["label"] for row in artifact["uncertainty_labels"]],
    )
