from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class SourceInput:
    id: str
    title: str
    text: str
    source_type: str = "note"

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
