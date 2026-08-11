"""Stable dependency boundaries for standalone and integrated deployments."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class WorkflowProfile(Protocol):
    profile_id: str
    display_name: str
    version: str
    purpose: str
    allowed_input_types: tuple[str, ...]
    claim_hints: tuple[str, ...]
    uncertainty_rules: tuple[str, ...]
    action_policy: tuple[str, ...]
    memory_policy: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    required_review_dimensions: tuple[str, ...]
    tags: tuple[str, ...]

    def build_uncertainties(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]: ...

    def build_inferences(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]: ...

    def build_actions(self, claim_ids: list[str], source_text: str) -> list[dict[str, Any]]: ...

    def build_memories(
        self,
        claims: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
        privacy_class: str,
    ) -> list[dict[str, Any]]: ...


@runtime_checkable
class ReviewStore(Protocol):
    def add(self, review: Any) -> None: ...

    def get(self, review_id: str) -> Any | None: ...

    def list_for_run(self, run_id: str) -> list[Any]: ...


@runtime_checkable
class MemoryStore(Protocol):
    def create(self, memory: Any) -> None: ...

    def get(self, memory_id: str) -> Any | None: ...

    def transition(self, memory_id: str, target_status: str, **context: Any) -> Any: ...

    def retrieve(self, query: str = "", **filters: Any) -> list[Any]: ...


@runtime_checkable
class KnowledgeMapStore(Protocol):
    def add_node(self, node: Any) -> None: ...

    def add_edge(self, edge: Any) -> None: ...

    def get_node(self, node_id: str) -> Any | None: ...

    def list_neighbours(self, node_id: str, edge_type: str | None = None) -> list[Any]: ...


@runtime_checkable
class GovernanceBackend(Protocol):
    def can_candidate_be_reviewed(self, candidate: Mapping[str, Any]) -> bool: ...

    def can_memory_be_promoted(self, memory: Any, review: Any) -> bool: ...

    def can_action_be_executed(self, action: Mapping[str, Any]) -> bool: ...

    def approver_for(self, operation: str) -> str: ...

    def policy_for(self, operation: str) -> Mapping[str, Any]: ...

    def audit_decision(self, operation: str, approved: bool, reasons: Iterable[str]) -> Mapping[str, Any]: ...
