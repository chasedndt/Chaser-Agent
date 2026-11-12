"""Hard limits the service enforces, whatever the model says: spend caps, a loop guard and approval timeouts.

Caps stop work rather than warn, because billing alerts arrive about a day after the money is spent. They
live in the service, not in the model's instructions, so a long conversation can't lose them.

- model_calls_per_day: every provider, counted on this computer. The guard against a runaway loop.
- credits_per_day and credits_per_session: what the route reports it charged (ChaseOS Cloud reports credits).
- repeat_limit: the same tool with the same arguments this many times in one turn is refused; twice refused, the turn stops.
- approval_timeout_minutes: an approval nobody answers in time becomes a "no", signed as automatic.

Zero turns a limit off. The day's totals are kept in agent/spend/<UTC date>.json.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

DEFAULTS = {"model_calls_per_day": 500, "credits_per_day": 0, "credits_per_session": 0, "repeat_limit": 3, "approval_timeout_minutes": 60}


@dataclass
class Limits:
    model_calls_per_day: int = DEFAULTS["model_calls_per_day"]
    credits_per_day: int = DEFAULTS["credits_per_day"]
    credits_per_session: int = DEFAULTS["credits_per_session"]
    repeat_limit: int = DEFAULTS["repeat_limit"]
    approval_timeout_minutes: int = DEFAULTS["approval_timeout_minutes"]

    @classmethod
    def from_settings(cls, value: dict[str, Any] | None) -> "Limits":
        names = {f.name for f in fields(cls)}
        clean = {}
        for name, raw in (value or {}).items():
            if name in names:
                try:
                    clean[name] = max(0, int(raw))
                except (TypeError, ValueError):
                    continue
        return cls(**clean)

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


class SpendLedger:
    """Today's model calls and credits across every session, kept on disk so a restart doesn't reset the cap."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self._lock = threading.Lock()

    def _path(self) -> Path:
        return self.folder / f"{time.strftime('%Y-%m-%d', time.gmtime())}.json"

    def today(self) -> dict[str, float]:
        try:
            value = json.loads(self._path().read_text(encoding="utf-8"))
            return {"calls": float(value.get("calls", 0)), "credits": float(value.get("credits", 0))}
        except (OSError, ValueError):
            return {"calls": 0.0, "credits": 0.0}

    def add(self, *, calls: int = 0, credits: float | None = None) -> dict[str, float]:
        with self._lock:
            value = self.today()
            value["calls"] += calls
            value["credits"] += float(credits or 0)
            self.folder.mkdir(parents=True, exist_ok=True)
            path = self._path()
            temporary = path.with_suffix(".partial")
            temporary.write_text(json.dumps(value), encoding="utf-8")
            temporary.replace(path)
            return value


def spend_stop(limits: Limits, ledger: SpendLedger, session_credits: float) -> str | None:
    """Why the next model call must not happen, or None."""
    today = ledger.today()
    if limits.model_calls_per_day and today["calls"] >= limits.model_calls_per_day:
        return (f"Today's cap of {limits.model_calls_per_day} model calls is reached, so this stopped before calling the model again. "
                "Raise it with: chaser limits set model_calls_per_day N")
    if limits.credits_per_day and today["credits"] >= limits.credits_per_day:
        return (f"Today's spend cap of {limits.credits_per_day} credits is reached ({today['credits']:.0f} used). "
                "Raise it with: chaser limits set credits_per_day N")
    if limits.credits_per_session and session_credits >= limits.credits_per_session:
        return (f"This session's spend cap of {limits.credits_per_session} credits is reached ({session_credits:.0f} used). "
                "Raise it with: chaser limits set credits_per_session N")
    return None
