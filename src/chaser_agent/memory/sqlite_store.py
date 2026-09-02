"""Append-only SQLite memory store with current-state retrieval."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from chaser_agent.memory.lifecycle import transition_memory
from chaser_agent.memory.models import MemoryFeedback, MemoryRecord, MemoryStatus
from chaser_agent.persistence import prepare_database_path


class SQLiteMemoryStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = prepare_database_path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_versions (
                    memory_id TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL,
                    memory_type TEXT NOT NULL, scope TEXT NOT NULL, privacy_class TEXT NOT NULL,
                    created_at TEXT NOT NULL, record_json TEXT NOT NULL, record_hash TEXT NOT NULL UNIQUE,
                    PRIMARY KEY (memory_id, version)
                );
                CREATE INDEX IF NOT EXISTS idx_memory_versions_lookup ON memory_versions(memory_id, version DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_versions_filters
                    ON memory_versions(status, scope, memory_type, created_at DESC);
                CREATE TABLE IF NOT EXISTS memory_feedback (
                    feedback_id TEXT PRIMARY KEY, memory_id TEXT NOT NULL, reviewer_id TEXT NOT NULL,
                    feedback TEXT NOT NULL, created_at TEXT NOT NULL, notes TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS governance_audits (
                    audit_id TEXT PRIMARY KEY, operation TEXT NOT NULL, approved INTEGER NOT NULL,
                    approved_by TEXT, created_at TEXT NOT NULL, audit_json TEXT NOT NULL
                );
                """
            )

    def create(self, memory: MemoryRecord) -> None:
        if memory.status not in {"raw", "candidate"}:
            raise ValueError("new memory must start as raw or candidate")
        try:
            with self._connect() as connection:
                self._insert_version(connection, memory, version=1)
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"memory already exists: {memory.memory_id}") from exc

    @staticmethod
    def _insert_version(connection: sqlite3.Connection, memory: MemoryRecord, version: int) -> None:
        connection.execute(
            """INSERT INTO memory_versions (
                memory_id, version, status, memory_type, scope, privacy_class,
                created_at, record_json, record_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory.memory_id, version, memory.status, memory.memory_type, memory.scope,
             memory.privacy_class, memory.created_at, memory.canonical_json(), memory.record_hash),
        )

    def get(self, memory_id: str) -> MemoryRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM memory_versions WHERE memory_id = ? ORDER BY version DESC LIMIT 1",
                (memory_id,),
            ).fetchone()
        return MemoryRecord.from_dict(json.loads(row["record_json"])) if row else None

    def history(self, memory_id: str) -> list[MemoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_json FROM memory_versions WHERE memory_id = ? ORDER BY version", (memory_id,)
            ).fetchall()
        return [MemoryRecord.from_dict(json.loads(row["record_json"])) for row in rows]

    def transition(self, memory_id: str, target_status: str, **context: Any) -> MemoryRecord:
        current = self.get(memory_id)
        if current is None:
            raise ValueError(f"memory not found: {memory_id}")
        if target_status == "promoted":
            audit_record = context.get("audit_record")
            if not isinstance(audit_record, dict) or audit_record.get("approved") is not True:
                raise ValueError("promoted transition requires an approved governance audit record")
            if not audit_record.get("approved_by"):
                raise ValueError("promotion audit must identify approved_by")
            context.setdefault("reviewer_id", audit_record["approved_by"])
        transitioned = transition_memory(
            current, target_status, reviewed_at=context.get("reviewed_at"),
            reviewer_id=context.get("reviewer_id"), promoted_at=context.get("promoted_at"),
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT MAX(version) AS version FROM memory_versions WHERE memory_id = ?", (memory_id,)
            ).fetchone()
            self._insert_version(connection, transitioned, int(row["version"]) + 1)
            if target_status == "promoted":
                audit = context["audit_record"]
                connection.execute(
                    "INSERT INTO governance_audits VALUES (?, ?, ?, ?, ?, ?)",
                    (audit["audit_id"], audit["operation"], 1, audit["approved_by"], audit["created_at"],
                     json.dumps(audit, ensure_ascii=False, sort_keys=True)),
                )
        return transitioned

    def retrieve(
        self, query: str = "", *, scope: str | None = None, memory_type: str | None = None,
        tags: tuple[str, ...] = (), statuses: tuple[MemoryStatus, ...] = ("promoted",), limit: int = 20,
    ) -> list[MemoryRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT record_json FROM memory_versions AS versions
                WHERE version = (SELECT MAX(current.version) FROM memory_versions AS current
                    WHERE current.memory_id = versions.memory_id)
                ORDER BY created_at DESC, memory_id"""
            ).fetchall()
        terms = tuple(term.casefold() for term in query.split() if term)
        required_tags = {tag.casefold() for tag in tags}
        results: list[MemoryRecord] = []
        for row in rows:
            record = MemoryRecord.from_dict(json.loads(row["record_json"]))
            if record.status not in statuses or (scope is not None and record.scope != scope):
                continue
            if memory_type is not None and record.memory_type != memory_type:
                continue
            if required_tags and not required_tags.issubset({tag.casefold() for tag in record.tags}):
                continue
            haystack = " ".join((record.content, *record.tags)).casefold()
            if terms and not all(term in haystack for term in terms):
                continue
            results.append(record)
            if len(results) >= limit:
                break
        return results

    def add_feedback(self, memory_id: str, reviewer_id: str, feedback: str, notes: str = "") -> MemoryFeedback:
        if self.get(memory_id) is None:
            raise ValueError(f"memory not found: {memory_id}")
        if feedback not in {"useful", "irrelevant", "stale", "disputed"}:
            raise ValueError("feedback must be useful, irrelevant, stale, or disputed")
        created_at = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        seed = f"{memory_id}\0{reviewer_id}\0{feedback}\0{created_at}\0{notes}"
        record = MemoryFeedback(
            feedback_id="feedback-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20],
            memory_id=memory_id, reviewer_id=reviewer_id, feedback=feedback,
            created_at=created_at, notes=notes,
        )
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO memory_feedback VALUES (?, ?, ?, ?, ?, ?)",
                (record.feedback_id, memory_id, reviewer_id, feedback, created_at, notes),
            )
        return record

    def list_feedback(self, memory_id: str) -> list[MemoryFeedback]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memory_feedback WHERE memory_id = ? ORDER BY created_at, feedback_id", (memory_id,)
            ).fetchall()
        return [MemoryFeedback(**dict(row)) for row in rows]

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT audit_json FROM governance_audits WHERE audit_id = ?", (audit_id,)
            ).fetchone()
        return json.loads(row["audit_json"]) if row else None
