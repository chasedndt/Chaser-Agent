from __future__ import annotations

import json
from pathlib import Path

import pytest

from chaser_agent.integrations.chaseos.adapter import ChaseOSProposalAdapter
from chaser_agent.knowledge.models import KnowledgeNode, stable_node_id
from chaser_agent.knowledge.service import index_reviewed_run
from chaser_agent.knowledge.sqlite_store import SQLiteKnowledgeMapStore
from chaser_agent.memory.service import reviewed_memories_from_review
from chaser_agent.memory.sqlite_store import SQLiteMemoryStore
from chaser_agent.reviews.service import create_review_record
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts


def _reviewed_run(tmp_path: Path):
    folder = tmp_path / "run"
    folder.mkdir()
    source = SourceInput(id="source-1", title="Source", text="The operator must preserve local provenance.")
    artifacts = build_source_card_artifacts(
        source, Path("source.md"), "run-1", "2026-08-11T12:00:00Z"
    )
    artifacts["run_log.json"] = {"run_id": "run-1"}
    for name, value in artifacts.items():
        (folder / name).write_text(json.dumps(value), encoding="utf-8")
    review = create_review_record(
        folder,
        reviewer_id="operator-1",
        scores=(3, 3, 3, 3, 3),
        decision="pass",
        reviewer_notes="Accepted.",
        accepted_action_ids=("action-001",),
        accepted_memory_ids=("memory-001",),
        reviewed_at="2026-08-11T12:10:00Z",
    )
    database = tmp_path / "state.db"
    memories = reviewed_memories_from_review(SQLiteMemoryStore(database), folder, review)
    store = SQLiteKnowledgeMapStore(database)
    counts = index_reviewed_run(store, folder, review, memories)
    return store, review, memories, counts


def test_stable_node_ids_are_deterministic():
    assert stable_node_id("claim", "source-1:claim-1", "run:run-1") == stable_node_id(
        "claim", "source-1:claim-1", "run:run-1"
    )
    assert stable_node_id("claim", "source-1:claim-1", "run:run-1") != stable_node_id(
        "claim", "source-1:claim-1", "run:run-2"
    )


def test_graph_queries_trace_reviewed_memory_to_source_claim_and_evidence(tmp_path: Path):
    store, review, memories, counts = _reviewed_run(tmp_path)
    entries = store.list_graph_entries_created_by_run("run-1")
    by_type = {}
    for node in entries["nodes"]:
        by_type.setdefault(node.node_type, []).append(node)

    source = by_type["source"][0]
    claim = by_type["claim"][0]
    memory = next(node for node in by_type["memory"] if node.label == memories[0].content)
    trace = store.trace_memory_to_source_and_evidence(memory.node_id)

    assert counts["nodes"] == len(entries["nodes"])
    assert counts["edges"] == len(entries["edges"])
    assert store.get_node(source.node_id) == source
    assert store.list_claims_derived_from_source(source.node_id) == [claim]
    assert store.list_evidence_supporting_claim(claim.node_id)
    assert store.list_memories_derived_from_source(source.node_id) == [memory]
    assert store.list_decisions_created_by_review(review.review_id)
    assert trace["sources"] == [source]
    assert trace["claims"] == [claim]
    assert trace["evidence"]


def test_deterministic_identity_collision_is_not_silently_overwritten(tmp_path: Path):
    store = SQLiteKnowledgeMapStore(tmp_path / "state.db")
    first = KnowledgeNode("node-1", "source", "A", "a", "scope", "public", "2026-08-11T12:00:00Z")
    second = KnowledgeNode("node-1", "source", "B", "b", "scope", "public", "2026-08-11T12:00:00Z")
    store.add_node(first)

    with pytest.raises(ValueError, match="identity collision"):
        store.add_node(second)


def test_chaseos_adapter_is_explicitly_inactive_and_cannot_dispatch():
    adapter = ChaseOSProposalAdapter()
    packet = adapter.proposal_packet("memory_candidate", {"memory_id": "mem-1"})

    assert adapter.active is False
    assert packet["dispatch_status"] == "not_dispatched"
    assert all(value is False for value in packet["authority"].values())
    with pytest.raises(RuntimeError, match="inactive"):
        adapter.dispatch(packet)
