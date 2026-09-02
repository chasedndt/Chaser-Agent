"""SQLite relationship index for Chaser Agent provenance."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from chaser_agent.knowledge.models import KnowledgeEdge, KnowledgeNode
from chaser_agent.persistence import prepare_database_path


class SQLiteKnowledgeMapStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = prepare_database_path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    node_id TEXT PRIMARY KEY, node_type TEXT NOT NULL, scope TEXT NOT NULL,
                    privacy_class TEXT NOT NULL, created_at TEXT NOT NULL,
                    run_id TEXT, review_id TEXT, node_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type, created_at);
                CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_run ON knowledge_nodes(run_id, node_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_review ON knowledge_nodes(review_id, node_type);
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    edge_id TEXT PRIMARY KEY, from_node_id TEXT NOT NULL, to_node_id TEXT NOT NULL,
                    edge_type TEXT NOT NULL, created_at TEXT NOT NULL, run_id TEXT, review_id TEXT,
                    edge_json TEXT NOT NULL,
                    FOREIGN KEY (from_node_id) REFERENCES knowledge_nodes(node_id),
                    FOREIGN KEY (to_node_id) REFERENCES knowledge_nodes(node_id)
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_from ON knowledge_edges(from_node_id, edge_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_to ON knowledge_edges(to_node_id, edge_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_run ON knowledge_edges(run_id, edge_type);
                """
            )

    def add_node(self, node: KnowledgeNode) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT node_json FROM knowledge_nodes WHERE node_id = ?", (node.node_id,)
            ).fetchone()
            if existing:
                if existing["node_json"] != node.canonical_json():
                    raise ValueError(f"deterministic node identity collision: {node.node_id}")
                return
            connection.execute(
                "INSERT INTO knowledge_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    node.node_id, node.node_type, node.scope, node.privacy_class, node.created_at,
                    node.metadata_json.get("run_id"), node.metadata_json.get("review_id"), node.canonical_json(),
                ),
            )

    def add_edge(self, edge: KnowledgeEdge) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT edge_json FROM knowledge_edges WHERE edge_id = ?", (edge.edge_id,)
            ).fetchone()
            if existing:
                if existing["edge_json"] != edge.canonical_json():
                    raise ValueError(f"deterministic edge identity collision: {edge.edge_id}")
                return
            connection.execute(
                "INSERT INTO knowledge_edges VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (edge.edge_id, edge.from_node_id, edge.to_node_id, edge.edge_type,
                 edge.created_at, edge.run_id, edge.review_id, edge.canonical_json()),
            )

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        with self._connect() as connection:
            row = connection.execute("SELECT node_json FROM knowledge_nodes WHERE node_id = ?", (node_id,)).fetchone()
        return KnowledgeNode.from_json(row["node_json"]) if row else None

    def _linked_nodes(self, node_id: str, edge_type: str, *, outgoing: bool, node_type: str | None = None) -> list[KnowledgeNode]:
        left, right = ("from_node_id", "to_node_id") if outgoing else ("to_node_id", "from_node_id")
        query = f"""SELECT nodes.node_json FROM knowledge_edges AS edges
            JOIN knowledge_nodes AS nodes ON nodes.node_id = edges.{right}
            WHERE edges.{left} = ? AND edges.edge_type = ?"""
        params: list[Any] = [node_id, edge_type]
        if node_type is not None:
            query += " AND nodes.node_type = ?"
            params.append(node_type)
        query += " ORDER BY nodes.created_at, nodes.node_id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [KnowledgeNode.from_json(row["node_json"]) for row in rows]

    def list_neighbours(self, node_id: str, edge_type: str | None = None) -> list[KnowledgeNode]:
        query = """SELECT DISTINCT nodes.node_json FROM knowledge_edges AS edges
            JOIN knowledge_nodes AS nodes
              ON nodes.node_id = CASE WHEN edges.from_node_id = ? THEN edges.to_node_id ELSE edges.from_node_id END
            WHERE (edges.from_node_id = ? OR edges.to_node_id = ?)"""
        params: list[Any] = [node_id, node_id, node_id]
        if edge_type is not None:
            query += " AND edges.edge_type = ?"
            params.append(edge_type)
        query += " ORDER BY nodes.created_at, nodes.node_id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [KnowledgeNode.from_json(row["node_json"]) for row in rows]

    def list_evidence_supporting_claim(self, claim_node_id: str) -> list[KnowledgeNode]:
        return self._linked_nodes(claim_node_id, "supported_by", outgoing=True, node_type="evidence")

    def list_claims_derived_from_source(self, source_node_id: str) -> list[KnowledgeNode]:
        return self._linked_nodes(source_node_id, "derived_from", outgoing=False, node_type="claim")

    def list_memories_derived_from_source(self, source_node_id: str) -> list[KnowledgeNode]:
        return self._linked_nodes(source_node_id, "derived_from", outgoing=False, node_type="memory")

    def list_decisions_created_by_review(self, review_id: str) -> list[KnowledgeNode]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT node_json FROM knowledge_nodes WHERE review_id = ? AND node_type = 'decision' ORDER BY node_id",
                (review_id,),
            ).fetchall()
        return [KnowledgeNode.from_json(row["node_json"]) for row in rows]

    def list_items_superseded_by_memory(self, memory_node_id: str) -> list[KnowledgeNode]:
        return self._linked_nodes(memory_node_id, "supersedes", outgoing=True)

    def list_graph_entries_created_by_run(self, run_id: str) -> dict[str, list[Any]]:
        with self._connect() as connection:
            node_rows = connection.execute(
                "SELECT node_json FROM knowledge_nodes WHERE run_id = ? ORDER BY node_id", (run_id,)
            ).fetchall()
            edge_rows = connection.execute(
                "SELECT edge_json FROM knowledge_edges WHERE run_id = ? ORDER BY edge_id", (run_id,)
            ).fetchall()
        return {
            "nodes": [KnowledgeNode.from_json(row["node_json"]) for row in node_rows],
            "edges": [KnowledgeEdge.from_json(row["edge_json"]) for row in edge_rows],
        }

    def trace_memory_to_source_and_evidence(self, memory_node_id: str) -> dict[str, Any]:
        memory = self.get_node(memory_node_id)
        if memory is None or memory.node_type != "memory":
            raise ValueError(f"memory node not found: {memory_node_id}")
        sources = self._linked_nodes(memory_node_id, "derived_from", outgoing=True, node_type="source")
        claims = self._linked_nodes(memory_node_id, "derived_from", outgoing=True, node_type="claim")
        evidence_by_id = {
            item.node_id: item
            for claim in claims
            for item in self.list_evidence_supporting_claim(claim.node_id)
        }
        return {"memory": memory, "sources": sources, "claims": claims, "evidence": list(evidence_by_id.values())}
