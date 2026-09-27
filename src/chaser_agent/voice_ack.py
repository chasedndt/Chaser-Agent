"""Play a fixed, public-safe acknowledgement through the local Pocket Alba API.

The transcript is never sent to the speech service. This is not an agent reply.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

ACK_TEXT = "I heard you. The draft transcript is ready for your review."
VOICE_PATH = re.compile(r"^/v1/voice/voice-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")
MAX_AUDIO_BYTES = 10_000_000


def speak_ack(*, data_dir: Path, port: int = 8765, timeout: float = 45.0) -> str:
    if not 1 <= port <= 65535:
        raise ValueError("Invalid local voice port")
    token_path = data_dir / "control-token"
    if data_dir.is_symlink() or token_path.is_symlink() or not token_path.is_file():
        raise ValueError("A real local voice token file is required")
    token = token_path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValueError("Local voice token is invalid")
    base = f"http://127.0.0.1:{port}"
    with urlopen(f"{base}/v1/health", timeout=3) as response:
        health = json.load(response)
    if health.get("voice_runtime") != "ready":
        raise RuntimeError("Local Pocket Alba voice is not ready")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps({"text": ACK_TEXT, "privacy_class": "public_toy"}).encode("utf-8")
    with urlopen(Request(f"{base}/v1/voice/replies", data=body, headers=headers, method="POST"), timeout=5) as response:
        job = json.load(response)
    path = job.get("status_url")
    if not isinstance(path, str) or not VOICE_PATH.fullmatch(path):
        raise RuntimeError("Local voice returned an invalid status path")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
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
            import winsound

            winsound.PlaySound(audio, winsound.SND_MEMORY)
            return str(status.get("voice_id"))
        if status.get("status") in {"failed", "interrupted"}:
            raise RuntimeError("Local voice take failed")
        time.sleep(0.5)
    raise TimeoutError("Local voice reply timed out")
