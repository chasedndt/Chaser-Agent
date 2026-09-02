"""Shared local persistence defaults."""

from __future__ import annotations

from pathlib import Path


def default_database_path() -> Path:
    """Return the user-owned database path outside the source repository."""
    return Path.home() / ".chaser-agent" / "chaser-agent.db"


def prepare_database_path(path: str | Path | None = None) -> Path:
    database_path = Path(path).expanduser() if path is not None else default_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return database_path
