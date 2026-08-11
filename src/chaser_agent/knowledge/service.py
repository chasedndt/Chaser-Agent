"""Build provenance graph entries from a reviewed source-card run."""

from __future__ import annotations

from pathlib import Path

from chaser_agent.knowledge.models import KnowledgeEdge, KnowledgeNode, stable_edge_id, stable_node_id
from chaser_agent.knowledge.sqlite_store import SQLiteKnowledgeMapStore
from chaser_agent.memory.models import MemoryRecord
from chaser_agent.reviews.models import ReviewRecord
from chaser_agent.reviews.service import load_review_material


def index_reviewed_run(
    store: SQLiteKnowledgeMapStore,
    run_folder: str | Path,
    review: ReviewRecord,
    memories: list[MemoryRecord],
) -> dict[str, int]:
    folder = Path(run_folder)
    material = load_review_material(folder)
    card = material["source_card.json"]
    run_id = review.run_id
    created_at = card["created_at"]
    privacy = card["privacy_class"]
    scope = "run"
    nodes: list[KnowledgeNode] = []
    edges: list[KnowledgeEdge] = []

    def node(node_type: str, identity: str, label: str, content_ref: str, *, metadata: dict | None = None) -> KnowledgeNode:
        values = {"run_id": run_id, **(metadata or {})}
        item = KnowledgeNode(
            node_id=stable_node_id(node_type, identity, f"run:{run_id}"),
            node_type=node_type,
            label=label,
            content_ref=content_ref,
            scope=scope,
            privacy_class=privacy,
            created_at=created_at,
            metadata_json=values,
        )
        nodes.append(item)
        return item

    def edge(
        edge_type: str,
        from_node: KnowledgeNode,
        to_node: KnowledgeNode,
        *,
        review_id: str | None = None,
    ) -> None:
        edges.append(
            KnowledgeEdge(
                edge_id=stable_edge_id(edge_type, from_node.node_id, to_node.node_id, run_id, review_id),
                from_node_id=from_node.node_id,
                to_node_id=to_node.node_id,
                edge_type=edge_type,
                created_at=created_at,
                run_id=run_id,
                review_id=review_id,
            )
        )

    run_node = node("run", run_id, run_id, str(folder / "run_log.json"))
    source_node = node("source", card["source_id"], card["source_title"], str(folder / "source_card.json"))
    workflow_node = node(
        "workflow", card["workflow_profile"], card["workflow_profile"], str(folder / "source_card.json")
    )
    edge("generated_in", source_node, run_node)
    edge("used_by", run_node, workflow_node)

    evidence_nodes: dict[str, KnowledgeNode] = {}
    for row in material["evidence_snippets.json"]["evidence_snippets"]:
        evidence_nodes[row["snippet_id"]] = node(
            "evidence", f"{card['source_id']}:{row['snippet_id']}", row["snippet_id"],
            f"{folder / 'evidence_snippets.json'}#{row['snippet_id']}",
        )

    claim_nodes: dict[str, KnowledgeNode] = {}
    for row in material["claims_table.json"]["claims"]:
        claim_node = node(
            "claim", f"{card['source_id']}:{row['claim_id']}", row["claim_text"],
            f"{folder / 'claims_table.json'}#{row['claim_id']}",
        )
        claim_nodes[row["claim_id"]] = claim_node
        edge("derived_from", claim_node, source_node)
        edge("supported_by", claim_node, evidence_nodes[row["evidence_snippet_id"]])
        edge("generated_in", claim_node, run_node)

    for row in card["chaser_agent_inferences"]:
        inference_node = node(
            "inference", f"{run_id}:{row['inference_id']}", row["inference_text"],
            f"{folder / 'source_card.json'}#{row['inference_id']}",
        )
        for claim_id in row["based_on_claim_ids"]:
            if claim_id in claim_nodes:
                edge("inferred_from", inference_node, claim_nodes[claim_id])
        edge("generated_in", inference_node, run_node)

    action_nodes: dict[str, KnowledgeNode] = {}
    for row in material["action_candidates.json"]["action_candidates"]:
        action_node = node(
            "action", f"{run_id}:{row['action_id']}", row["action_text"],
            f"{folder / 'action_candidates.json'}#{row['action_id']}",
        )
        action_nodes[row["action_id"]] = action_node
        edge("proposed_by", action_node, run_node)
        edge("generated_in", action_node, run_node)

    decision_node = node(
        "decision", review.review_id, f"Review decision: {review.decision}", f"sqlite:review_records/{review.review_id}",
        metadata={"review_id": review.review_id, "decision": review.decision},
    )
    edge("reviewed_in", decision_node, run_node, review_id=review.review_id)
    for action_id in review.accepted_action_ids:
        edge("approved_by", action_nodes[action_id], decision_node, review_id=review.review_id)
    for action_id in review.rejected_action_ids:
        edge("rejected_by", action_nodes[action_id], decision_node, review_id=review.review_id)

    for memory in memories:
        memory_node = node(
            "memory", memory.memory_id, memory.content, f"sqlite:memory_versions/{memory.memory_id}",
            metadata={"review_id": review.review_id, "status": memory.status},
        )
        for source_ref in memory.source_refs:
            if source_ref == card["source_id"]:
                edge("derived_from", memory_node, source_node, review_id=review.review_id)
        for claim_ref in memory.claim_refs:
            if claim_ref in claim_nodes:
                edge("derived_from", memory_node, claim_nodes[claim_ref], review_id=review.review_id)
        edge("reviewed_in", memory_node, decision_node, review_id=review.review_id)
        edge("generated_in", memory_node, run_node, review_id=review.review_id)

    for item in nodes:
        store.add_node(item)
    for item in edges:
        store.add_edge(item)
    return {"nodes": len(nodes), "edges": len(edges)}
