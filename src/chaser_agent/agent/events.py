"""Append-only, hash-chained session events: what actually happened, in order.

Judge an agent by its effects rather than its closing message. A person or a test
reads this log to see every model request, tool call, denial and decision; the
chain makes a silently edited line detectable.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

GENESIS = "0" * 64
IO_ATTEMPTS = 6
T = TypeVar("T")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def with_io_retry(operation: Callable[[], T]) -> T:
    """Survive brief file errors. Windows can refuse an open while a scanner holds the path."""
    for attempt in range(IO_ATTEMPTS):
        try:
            return operation()
        except OSError:
            if attempt == IO_ATTEMPTS - 1:
                raise
            time.sleep(0.05 * 2**attempt)
    raise AssertionError("unreachable")


# Receipts are meant to be shown to people, so secrets never go into them: values under secret-sounding
# names, and strings shaped like well-known keys and tokens, are replaced before the event is hashed.
SECRET_NAMES = re.compile(r"(pass(word)?|secret|token|api[_-]?key|authorization|auth|credential|private[_-]?key|cookie|session[_-]?key)$", re.I)
SECRET_SHAPES = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|sk-ant-[A-Za-z0-9_-]{16,}|xox[abprs]-[A-Za-z0-9-]{10,}|xapp-[A-Za-z0-9-]{10,}|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"
    r"|Bearer\s+[A-Za-z0-9._~+/-]{16,}=*|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)")
REDACTED = "[redacted]"


def redact(value: Any, name: str = "") -> Any:
    """A copy with secrets replaced; digests and ids keep their names, so only key-like values change."""
    if isinstance(value, dict):
        return {k: redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, name) for v in value]
    if isinstance(value, str):
        if name and SECRET_NAMES.search(name) and value and name.lower() not in {"digest", "prompt_sha256", "reply_sha256"}:
            return REDACTED
        return SECRET_SHAPES.sub(REDACTED, value)
    return value


def _digest(row: dict[str, Any]) -> str:
    body = {key: value for key, value in row.items() if key != "hash"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._rows: list[dict[str, Any]] = []
        if path.exists():
            text = with_io_retry(lambda: path.read_text(encoding="utf-8"))
            # Only "\n" ends an event: document text may hold other Unicode line separators.
            self._rows = [json.loads(line) for line in text.split("\n") if line.strip()]

    def append(self, event_type: str, /, **data: Any) -> dict[str, Any]:
        data = redact(data)
        with self._lock:
            row = {
                "seq": len(self._rows) + 1,
                "at": utc_now(),
                "type": event_type,
                "data": data,
                "prev": self._rows[-1]["hash"] if self._rows else GENESIS,
            }
            row["hash"] = _digest(row)
            line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"

            def write() -> None:
                with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(line)

            with_io_retry(write)
            self._rows.append(row)
            return row

    def after(self, seq: int, limit: int = 500) -> list[dict[str, Any]]:
        with self._lock:
            return self._rows[seq : seq + limit]

    def __len__(self) -> int:
        with self._lock:
            return len(self._rows)


def verify_chain(path: Path) -> dict[str, Any]:
    """Re-derive every hash from disk. Detects drift; it does not make the file immutable."""
    previous = GENESIS
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            count += 1
            if row["prev"] != previous or _digest(row) != row["hash"] or row["seq"] != count:
                return {"verified": False, "failed_at": count, "events": count}
            previous = row["hash"]
    return {"verified": True, "events": count, "head": previous}
