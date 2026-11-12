"""Where Chaser keeps its own settings on this computer, outside the private data folder.

The settings say where the data folder is, so they can't live inside it. They hold no secrets:
the ChaseOS Cloud key is kept separately and encrypted (see cloud_key.py).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

HOME_ENV = "CHASER_AGENT_HOME"
SETTINGS_FILE = "settings.json"
DEFAULT_PORT = 8765
DEFAULT_MEMORY_LIMIT_MB = 1500
DEFAULT_SHORTCUTS = {"stop": "Ctrl+Alt+Pause", "stop_fallback": "Ctrl+Alt+Shift+S", "take_over": "Ctrl+Alt+Shift+T"}
FIELDS = {"data_dir", "port", "packs", "reviewer", "memory_limit_mb", "shortcuts", "onboarded_at"}


def home() -> Path:
    """%LOCALAPPDATA%\\ChaserAgent on Windows, ~/.chaser-agent elsewhere, or CHASER_AGENT_HOME."""
    if os.environ.get(HOME_ENV):
        return Path(os.environ[HOME_ENV])
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "ChaserAgent"
    return Path.home() / ".chaser-agent"


def defaults() -> dict[str, Any]:
    return {"data_dir": str(home() / "data"), "port": DEFAULT_PORT, "packs": [], "reviewer": "",
            "memory_limit_mb": DEFAULT_MEMORY_LIMIT_MB, "shortcuts": dict(DEFAULT_SHORTCUTS), "onboarded_at": None}


def settings_path() -> Path:
    return home() / SETTINGS_FILE


def load() -> dict[str, Any]:
    """Saved settings over the defaults. A missing or unreadable file gives the defaults."""
    value = defaults()
    try:
        saved = json.loads(settings_path().read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return value
    if isinstance(saved, dict):
        for key in FIELDS & set(saved):
            value[key] = saved[key]
        value["shortcuts"] = {**DEFAULT_SHORTCUTS, **(saved.get("shortcuts") or {})}
    return value


def save(changes: dict[str, Any]) -> dict[str, Any]:
    """Merge changes into the saved settings and write them atomically."""
    unknown = set(changes) - FIELDS
    if unknown:
        raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
    value = {**load(), **changes}
    if "shortcuts" in changes:
        value["shortcuts"] = {**DEFAULT_SHORTCUTS, **load()["shortcuts"], **changes["shortcuts"]}
    target = settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".settings-", dir=target.parent)
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=1, ensure_ascii=False)
        stream.write("\n")
    os.replace(temporary, target)
    return value


def is_onboarded() -> bool:
    return bool(load().get("onboarded_at"))
