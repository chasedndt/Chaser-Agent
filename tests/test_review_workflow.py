from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from chaser_agent.cli import main
from chaser_agent.governance.local import LocalGovernance
from chaser_agent.memory.sqlite_store import SQLiteMemoryStore
from chaser_agent.reviews.models import ReviewRecord
from chaser_agent.reviews.service import artifact_hashes, create_review_record
from chaser_agent.reviews.sqlite_store import DuplicateReviewError, SQLiteReviewStore
from chaser_agent.schemas import SourceInput
from chaser_agent.source_card import build_source_card_artifacts


def _review(**overrides) -> ReviewRecord:
    values = {
        "review_id": "review-1",
        "run_id": "run-1",
        "reviewer_id": "operator-1",
        "reviewed_at": "2026-08-11T12:00:00Z",
        "source_fidelity_score": 3,
        "inference_separation_score": 3,
        "uncertainty_handling_score": 2,
        "action_usefulness_score": 2,
        "memory_safety_score": 3,
        "decision": "pass",
        "reviewer_notes": "Source grounded.",
        "accepted_memory_ids": ("memory-001",),
    }
    values.update(overrides)
    return ReviewRecord(**values)


def _run_folder(tmp_path: Path) -> Path:
    folder = tmp_path / "run"
    folder.mkdir()
    source = SourceInput(id="source-1", title="Source", text="This policy must remain local.")
    artifacts = build_source_card_artifacts(
        source,
        Path("source.md"),
        run_id="run-1",
        created_at="2026-08-11T12:00:00Z",
    )
    artifacts["run_log.json"] = {"run_id": "run-1"}
    for name, value in artifacts.items():
        (folder / name).write_text(json.dumps(value, indent=2), encoding="utf-8")
    return folder


def test_review_record_validates_scores_and_decisions():
    assert _review().total_score == 13
    with pytest.raises(ValueError, match="0 through 3"):
        _review(source_fidelity_score=4)
    with pytest.raises(ValueError, match="decision"):
        _review(decision="approved")


def test_review_store_is_insert_only_and_round_trips(tmp_path: Path):
    store = SQLiteReviewStore(tmp_path / "reviews.db")
    review = _review()

    store.add(review)

    assert store.get(review.review_id) == review
    assert store.list_for_run("run-1") == [review]
    with pytest.raises(DuplicateReviewError, match="immutable"):
        store.add(review)


def test_review_creation_validates_candidate_ids_and_preserves_artifacts(tmp_path: Path):
    folder = _run_folder(tmp_path)
    before = artifact_hashes(folder)

    review = create_review_record(
        folder,
        reviewer_id="operator-1",
        scores=(3, 3, 2, 2, 3),
        decision="pass",
        reviewer_notes="Accepted for local review state.",
        accepted_action_ids=("action-001",),
        accepted_memory_ids=("memory-001",),
        reviewed_at="2026-08-11T12:00:00Z",
    )

    assert review.run_id == "run-1"
    assert artifact_hashes(folder) == before
    with pytest.raises(ValueError, match="unknown memory candidate ID"):
        create_review_record(
            folder,
            reviewer_id="operator-1",
            scores=(3, 3, 2, 2, 3),
            decision="pass",
            reviewer_notes="",
            accepted_memory_ids=("missing",),
        )


def test_review_cli_persists_record_without_promotion(tmp_path: Path, capsys):
    folder = _run_folder(tmp_path)
    database = tmp_path / "state.db"
    before = artifact_hashes(folder)

    result = main(
        [
            "review",
            str(folder),
            "--database",
            str(database),
            "--reviewer-id",
            "operator-1",
            "--source-fidelity-score",
            "3",
            "--inference-separation-score",
            "3",
            "--uncertainty-handling-score",
            "2",
            "--action-usefulness-score",
            "2",
            "--memory-safety-score",
            "3",
            "--decision",
            "pass",
            "--accept-memory",
            "memory-001",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["memory_promotion"] == "not_performed"
    assert len(output["memory_records_created"]) == 1
    assert SQLiteMemoryStore(database).get(output["memory_records_created"][0]).status == "reviewed"
    assert output["original_artifacts_unchanged"] is True
    assert len(SQLiteReviewStore(database).list_for_run("run-1")) == 1
    assert artifact_hashes(folder) == before


def test_local_governance_requires_reviewed_accepted_memory_and_disables_execution():
    governance = LocalGovernance("operator-1")
    review = _review()
    reviewed = SimpleNamespace(memory_id="memory-001", status="reviewed")
    candidate = SimpleNamespace(memory_id="memory-001", status="candidate")

    assert governance.can_memory_be_promoted(reviewed, review) is True
    assert governance.can_memory_be_promoted(candidate, review) is False
    assert governance.can_action_be_executed({"action_id": "action-001"}) is False
    assert governance.policy_for("memory.promote")["review_policy_proposal"]["enforced"] is False
