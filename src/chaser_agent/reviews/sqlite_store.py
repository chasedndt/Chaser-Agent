"""Insert-only SQLite review store."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from chaser_agent.persistence import prepare_database_path
from chaser_agent.reviews.models import ReviewRecord


class DuplicateReviewError(ValueError):
    pass


class SQLiteReviewStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = prepare_database_path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_records (
                    review_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    total_score INTEGER NOT NULL,
                    record_json TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_review_records_run_id ON review_records(run_id, reviewed_at)"
            )

    def add(self, review: ReviewRecord) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO review_records (
                        review_id, run_id, reviewer_id, reviewed_at, decision,
                        total_score, record_json, record_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review.review_id,
                        review.run_id,
                        review.reviewer_id,
                        review.reviewed_at,
                        review.decision,
                        review.total_score,
                        review.canonical_json(),
                        review.record_hash,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateReviewError(f"review record is immutable and already exists: {review.review_id}") from exc

    def get(self, review_id: str) -> ReviewRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM review_records WHERE review_id = ?", (review_id,)
            ).fetchone()
        return ReviewRecord.from_dict(json.loads(row["record_json"])) if row else None

    def list_for_run(self, run_id: str) -> list[ReviewRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM review_records WHERE run_id = ? ORDER BY reviewed_at, review_id",
                (run_id,),
            ).fetchall()
        return [ReviewRecord.from_dict(json.loads(row["record_json"])) for row in rows]
