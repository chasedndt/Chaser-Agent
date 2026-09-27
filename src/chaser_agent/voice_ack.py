"""Play fixed or tightly bounded read-only replies through local Pocket Alba.

The transcript is never sent to the speech service. This is not an agent reply.
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

from chaser_agent.local_acl import read_private_control_token
from chaser_agent.voice_status import public_status_reply, status_intent

ACK_TEXT = "I heard you. The draft transcript is ready for your review."
VOICE_PATH = re.compile(r"^/v1/voice/voice-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")
MAX_AUDIO_BYTES = 10_000_000


def _request_cancel(*, base: str, token: str, path: str) -> None:
    """Best-effort stop for the exact take this client requested."""
    if not VOICE_PATH.fullmatch(path):
        return
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with urlopen(Request(base + path + "/cancel", data=b"{}", headers=headers, method="POST"), timeout=3):
            pass
    except (OSError, ValueError):
        pass


def speak_ack(*, data_dir: Path, port: int = 8765, timeout: float = 45.0) -> str:
    if not 1 <= port <= 65535:
        raise ValueError("Invalid local voice port")
    token = read_private_control_token(data_dir)
    base = f"http://127.0.0.1:{port}"
    with urlopen(f"{base}/v1/health", timeout=3) as response:
        health = json.load(response)
    if health.get("voice_runtime") != "ready":
        raise RuntimeError("Local Pocket Alba voice is not ready")
    return _play_public_text(base=base, token=token, text=ACK_TEXT, timeout=timeout)


def speak_status_reply(*, data_dir: Path, transcript: str,
                       port: int = 8765, timeout: float = 45.0,
                       cancel_event: threading.Event | None = None) -> tuple[str, str] | None:
    """Answer only an exact read-only status question, never a command."""
    intent = status_intent(transcript)
    if intent is None:
        return None
    if not 1 <= port <= 65535:
        raise ValueError("Invalid local voice port")
    token = read_private_control_token(data_dir)
    base = f"http://127.0.0.1:{port}"
    with urlopen(f"{base}/v1/health", timeout=3) as response:
        health = json.load(response)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with urlopen(Request(f"{base}/v1/hud/current", headers=headers), timeout=3) as response:
        hud = json.load(response)
    reply = public_status_reply(intent=intent, health=health, hud=hud, port=port)
    if health.get("voice_runtime") != "ready":
        raise RuntimeError("Local Pocket Alba voice is not ready")
    return reply, _play_public_text(
        base=base, token=token, text=reply, timeout=timeout, cancel_event=cancel_event,
    )


def _play_public_text(*, base: str, token: str, text: str, timeout: float,
                      cancel_event: threading.Event | None = None) -> str:
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError("Local speech playback cancelled")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps({"text": text, "privacy_class": "public_toy"}).encode("utf-8")
    with urlopen(Request(f"{base}/v1/voice/replies", data=body, headers=headers, method="POST"), timeout=5) as response:
        job = json.load(response)
    path = job.get("status_url")
    if not isinstance(path, str) or not VOICE_PATH.fullmatch(path):
        raise RuntimeError("Local voice returned an invalid status path")
    completed = False
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError("Local speech playback cancelled")
            with urlopen(Request(base + path, headers=headers), timeout=5) as response:
                status = json.load(response)
            if status.get("status") == "generated_pending_listening_review":
                audio_path = status.get("audio_url")
                if audio_path != path + "/audio.wav":
                    raise RuntimeError("Local voice returned an invalid audio path")
                with urlopen(Request(base + audio_path, headers=headers), timeout=5) as response:
                    audio = response.read(MAX_AUDIO_BYTES + 1)
                if len(audio) > MAX_AUDIO_BYTES or not audio.startswith(b"RIFF"):
                    raise RuntimeError("Local voice returned an invalid WAV")
                if cancel_event is not None and cancel_event.is_set():
                    raise RuntimeError("Local speech playback cancelled")
                import winsound

                winsound.PlaySound(audio, winsound.SND_MEMORY)
                completed = True
                return str(status.get("voice_id"))
            if status.get("status") in {"failed", "interrupted", "cancelled"}:
                raise RuntimeError("Local voice take failed")
            time.sleep(0.5)
        raise TimeoutError("Local voice reply timed out")
    finally:
        if not completed:
            _request_cancel(base=base, token=token, path=path)
