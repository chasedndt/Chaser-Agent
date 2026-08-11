"""Compatibility helpers for the original scaffold memory API."""

from chaser_agent.memory.lifecycle import VALID_TRANSITIONS
from chaser_agent.memory.models import MEMORY_STATUSES

MEMORY_STATES = list(MEMORY_STATUSES)


def next_review_state(current: str) -> str:
    compatibility = {"raw context": "candidate", "candidate memory": "reviewed"}
    normalized = compatibility.get(current, current.replace(" memory", ""))
    if normalized == "raw":
        return "candidate"
    if normalized == "candidate":
        return "reviewed"
    return normalized if normalized in VALID_TRANSITIONS else current
