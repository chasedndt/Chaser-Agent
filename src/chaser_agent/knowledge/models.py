"""Knowledge-map node and edge models with deterministic identity."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

NODE_TYPES = frozenset({
    "source", "claim", "evidence", "inference", "concept", "decision", "action", "memory",
    "workflow", "run", "project", "skill", "agent", "tool",
})
EDGE_TYPES = frozenset({
    "derived_from", "supported_by", "contradicts", "inferred_from", "relates_to", "applies_to",
    "proposed_by", "approved_by", "rejected_by", "supersedes", "generated_in", "used_by", "reviewed_in",
})


def stable_node_id(node_type: str, content_identity: str, scope: str) -> str:
    return f"node-{uuid.uuid5(uuid.NAMESPACE_URL, f'chaser-agent:node:{node_type}:{scope}:{content_identity}')}"


def stable_edge_id(
    edge_type: str,
    from_node_id: str,
    to_node_id: str,
    run_id: str | None = None,
    review_id: str | None = None,
) -> str:
    identity = f"chaser-agent:edge:{edge_type}:{from_node_id}:{to_node_id}:{run_id or ''}:{review_id or ''}"
    return f"edge-{uuid.uuid5(uuid.NAMESPACE_URL, identity)}"


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    node_type: str
    label: str
    content_ref: str
    scope: str
    privacy_class: str
    created_at: str
    metadata_json: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.node_type not in NODE_TYPES:
            raise ValueError(f"unsupported node type: {self.node_type}")

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "KnowledgeNode":
        return cls(**json.loads(value))


@dataclass(frozen=True)
class KnowledgeEdge:
    edge_id: str
    from_node_id: str
    to_node_id: str
    edge_type: str
    created_at: str
    run_id: str | None = None
    review_id: str | None = None
    metadata_json: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.edge_type not in EDGE_TYPES:
            raise ValueError(f"unsupported edge type: {self.edge_type}")

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, value: str) -> "KnowledgeEdge":
        return cls(**json.loads(value))
