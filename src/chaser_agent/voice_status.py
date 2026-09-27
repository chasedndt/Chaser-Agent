"""Narrow read-only replies to explicit local-service status questions.

An unverified transcript can select one of these harmless queries. It cannot
become a tool command, an action summary, or speech content itself.
"""

from __future__ import annotations

import re

STATUS_QUESTIONS = frozenset({
    "what is your status", "what s your status", "whats your status",
    "what is chaser agent status", "what is the local service status",
    "is computer use active", "are you using my computer",
})
PORT_QUESTIONS = frozenset({
    "what port are you running on", "which port are you running on",
    "what is your port", "what s your port", "whats your port",
})
PHASES = {
    "running": "running", "awaiting_approval": "waiting for approval",
    "paused": "paused", "stopped": "stopped", "completed": "completed",
    "failed": "failed",
}


def status_intent(transcript: str) -> str | None:
    if not isinstance(transcript, str) or len(transcript) > 2000:
        return None
    normalized = re.sub(r"[^a-z0-9]+", " ", transcript.lower()).strip()
    normalized = " ".join(normalized.split())
    if normalized in STATUS_QUESTIONS:
        return "status"
    if normalized in PORT_QUESTIONS:
        return "port"
    return None


def public_status_reply(*, intent: str, health: dict[str, object],
                        hud: dict[str, object], port: int) -> str:
    if (health.get("service") != "chaser-agent" or health.get("status") != "ready"
            or health.get("port") != port or health.get("bind") != "127.0.0.1"
            or not isinstance(health.get("mode"), str)
            or health["mode"] not in {"deterministic_review_only", "review_with_local_voice"}):
        raise ValueError("The local service identity is not verified")
    if intent == "port":
        return f"Chaser Agent's local review service is on port {port}, bound to this computer only."
    if intent != "status":
        raise ValueError("Unsupported read-only status question")
    if hud.get("status") == "inactive":
        return f"The local review service is ready on port {port}. No computer-use executor is connected."
    phase = hud.get("phase")
    if hud.get("connected") is not True:
        return f"The local review service is ready on port {port}. Computer-use status is uncertain because its connection is lost."
    if not isinstance(phase, str) or phase not in PHASES:
        return f"The local review service is ready on port {port}. I cannot verify a computer-use phase."
    return f"The local review service is ready on port {port}. A computer-use session reports {PHASES[phase]}."
