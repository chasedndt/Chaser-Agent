from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

PrivacyClass = Literal["public_toy", "public", "scrubbed", "internal_safe", "toy"]
ReviewStatus = Literal["pending_review", "pending", "reviewed", "needs_revision", "rejected"]
PromotionStatus = Literal["not_promoted", "candidate_only", "blocked", "approved_elsewhere", "rejected"]

@dataclass
class SourceInput:
    id: str
    title: str
    text: str
    source_type: str = "note"
    source_origin: str = "operator_provided_safe_local_file"
    privacy_class: str = "public_toy"

@dataclass
class Claim:
    text: str
    evidence: str
    uncertainty: str = "not_reviewed"

@dataclass
class ActionCandidate:
    text: str
    rationale: str
    source_id: str
    status: str = "candidate"

@dataclass
class MemoryCandidate:
    text: str
    evidence: str
    state: str = "candidate"

@dataclass
class SourceCard:
    source_id: str
    title: str
    summary: str
    claims: list[Claim] = field(default_factory=list)
    actions: list[ActionCandidate] = field(default_factory=list)
    memory_candidates: list[MemoryCandidate] = field(default_factory=list)
    uncertainty_labels: list[str] = field(default_factory=list)

class SourceClaimRow(TypedDict):
    claim_id: str
    claim_text: str
    evidence_snippet_id: str
    source_location: str
    claim_type: str
    confidence: str
    review_note: str

class EvidenceSnippetRow(TypedDict):
    snippet_id: str
    text: str
    source_location: str
    supports_claim_ids: list[str]
    privacy_class: str
    redaction_note: str | None

class UncertaintyLabelRow(TypedDict):
    uncertainty_id: str
    label: str
    explanation: str
    related_claim_ids: list[str]

class InferenceRow(TypedDict):
    inference_id: str
    inference_text: str
    based_on_claim_ids: list[str]
    confidence: str
    uncertainty_label_ids: list[str]

class ActionCandidateRow(TypedDict):
    action_id: str
    action_text: str
    source_claim_ids: list[str]
    rationale: str
    risk_level: str
    requires_approval: bool
    blocked_reason: str | None
    suggested_owner: str

class MemoryCandidateRow(TypedDict):
    memory_candidate_id: str
    candidate_text: str
    evidence_snippet_id: str
    scope: str
    stability: str
    privacy_class: str
    promotion_status: str
    review_required: bool
    rejection_reason: str | None

@dataclass
class EvalCase:
    id: str
    task: str
    input: dict[str, Any]
    expected: dict[str, Any] = field(default_factory=dict)
    rubric: dict[str, float] = field(default_factory=dict)

@dataclass
class EvalResult:
    id: str
    task: str
    passed: bool
    score: float
    notes: str
    output: dict[str, Any] = field(default_factory=dict)
