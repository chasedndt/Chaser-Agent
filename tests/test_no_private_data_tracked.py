"""Keep private operational data out of a public repository.

This repository is public and MIT-licensed. ChaseOS vault logs, operator briefs,
Discord channel identifiers, private social pilot accounts, and local machine
paths are internal operating context: useful inside ChaseOS, wrong on GitHub.

Removing them once is not enough — the same content has been reintroduced by
routine mirroring before. These tests make the boundary executable, so a future
pass cannot quietly add it back.

Scope: git-tracked files only. Untracked local copies are deliberately allowed;
the operator keeps working notes on disk without publishing them.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Directories that mirror the ChaseOS vault. They must never be tracked here.
FORBIDDEN_TRACKED_PREFIXES = ("07_LOGS/", "99_ARCHIVE/")

PRIVATE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Discord snowflake identifiers for private channels.
    ("discord_channel_id", re.compile(r"\b1[0-9]{17,18}\b")),
    # The operator's private ChaseOS vault.
    ("chaseos_vault_path", re.compile(r"chaseos_obsidian")),
    # Local machine paths that expose the operator's filesystem layout.
    ("windows_user_path", re.compile(r"[A-Za-z]:\\Users\\chaseos", re.IGNORECASE)),
    ("wsl_user_path", re.compile(r"/mnt/[a-z]/Users/chaseos", re.IGNORECASE)),
    ("unix_home_path", re.compile(r"/home/chaseos")),
    # Private social pilot identifiers.
    ("pilot_social_account", re.compile(r"@chaseos_ai\b")),
)

TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".jsonl", ".txt", ".toml", ".cfg", ".ini"}

# This module necessarily contains the patterns it forbids.
SELF = "tests/test_no_private_data_tracked.py"


def tracked_text_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return [
        name
        for name in result.stdout.split()
        if name != SELF and Path(name).suffix.lower() in TEXT_SUFFIXES
    ]


def test_chaseos_vault_directories_are_not_tracked():
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=False)
    tracked = [
        name for name in result.stdout.split() if name.startswith(FORBIDDEN_TRACKED_PREFIXES)
    ]
    assert not tracked, (
        "ChaseOS vault logs must stay local and untracked; found "
        f"{len(tracked)} tracked file(s): " + ", ".join(tracked[:10])
    )


@pytest.mark.parametrize("label,pattern", PRIVATE_PATTERNS, ids=[name for name, _ in PRIVATE_PATTERNS])
def test_no_private_identifiers_in_tracked_files(label: str, pattern: re.Pattern[str]):
    offenders: list[str] = []
    for name in tracked_text_files():
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                offenders.append(f"{name}:{number}")
    assert not offenders, (
        f"private data ({label}) is tracked in a public repository: "
        + ", ".join(offenders[:15])
    )


def test_detectors_actually_match_their_targets():
    """Guard against a pattern silently ceasing to match anything."""
    samples = {
        "discord_channel_id": "channel 1518390727095095479",
        "chaseos_vault_path": "Documents/chaseos_obsidian/b/s",
        "windows_user_path": "C:" + chr(92) + "Users" + chr(92) + "chaseos" + chr(92) + "x",
        "wsl_user_path": "/mnt/c/Users/chaseos/Documents",
        "unix_home_path": "/home/chaseos/.local",
        "pilot_social_account": "posting as @chaseos_ai today",
    }
    for label, pattern in PRIVATE_PATTERNS:
        assert pattern.search(samples[label]), f"{label} pattern no longer matches its sample"
