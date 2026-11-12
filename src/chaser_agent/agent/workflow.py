"""A workflow narrows what a session may do. It never widens authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowSpec:
    workflow_id: str
    title: str
    instructions: str
    grants: frozenset[str]
    triggers: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    max_steps: int = 40
    max_seconds: int = 3_600
    # Score each turn before it may stop (agent/objective.py); off unless a workflow asks for it.
    objective_check: bool = False
    # Sources a matching request must have read before it may stop (objective.Requirement).
    objective_requires: tuple[Any, ...] = ()
    # Optional claim verifier (objective.verify_claims): checks a passing final answer against the sources read.
    objective_verifier: Any = None

    def __post_init__(self) -> None:
        if not self.workflow_id.strip() or not self.instructions.strip():
            raise ValueError("a workflow needs an id and instructions")
        if self.max_steps <= 0 or self.max_seconds <= 0:
            raise ValueError("workflow budgets must be positive")

    def matches(self, message: str) -> bool:
        lowered = message.lower()
        return any(trigger in lowered for trigger in self.triggers)
