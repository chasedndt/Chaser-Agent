"""Optional, offline Pocket Alba response adapter for a local Chaser instance.

The speech library is operator-supplied at startup. HTTP callers cannot select
an executable, model, voice, output path, or provider. A generated take still
requires listening review; this module does not make it canonical media.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path

VOICE_ID = re.compile(r"^voice-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")
MAX_SPEECH_CHARS = 500
MAX_WAV_BYTES = 20_000_000


class VoiceBusy(RuntimeError):
    pass


class VoiceGenerationFailed(RuntimeError):
    pass


class PocketAlbaVoice:
    def __init__(self, *, library_root: Path, data_dir: Path):
        if library_root.is_symlink():
            raise ValueError("Voice library must not be a symlink")
        self.library_root = library_root.resolve(strict=True)
        self.data_dir = data_dir.resolve()
        manifest = json.loads((self.library_root / "voice-library.json").read_text(encoding="utf-8"))
        approved = manifest.get("chaser_agent_production_voice", {})
        if approved.get("voice_id") != "pocket-alba" or "operator-approved" not in approved.get("status", ""):
            raise ValueError("The configured library does not identify the approved Pocket Alba voice")
        runtime = manifest.get("runtime_paths", {})
        for key in ("pocket_python", "pocket_config", "pocket_voices"):
            if not isinstance(runtime.get(key), str) or not Path(runtime[key]).exists():
                raise ValueError(f"The local voice runtime is missing {key}")
        if not (Path(runtime["pocket_voices"]) / "alba.safetensors").is_file():
            raise ValueError("The local Pocket Alba preset is missing")
        self.launcher = self.library_root / "Speech.ps1"
        self.script = self.library_root / "scripts" / "speech.py"
        self.python = Path(runtime["pocket_python"])
        if not self.launcher.is_file() or not self.script.is_file():
            raise ValueError("The local speech launcher and script are required")
        self.voice_root = self.data_dir / "voice"
        self.voice_root.mkdir(parents=True, exist_ok=True)
        self._generation_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._jobs: dict[str, dict[str, object]] = {}
        self._process: subprocess.Popen[str] | None = None
        self._worker_thread: threading.Thread | None = None
        self._closed = False

    def enqueue(self, text: str) -> dict[str, object]:
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_SPEECH_CHARS:
            raise ValueError("Voice text must contain 1–500 characters")
        if not self._generation_lock.acquire(blocking=False):
            raise VoiceBusy("A local voice take is already generating")
        try:
            if self._closed:
                raise VoiceGenerationFailed("The local voice adapter is closed")
            voice_id = f"voice-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}-{secrets.token_hex(6)}"
            folder = self.voice_root / voice_id
            folder.mkdir(exist_ok=False)
            (folder / "script.txt").write_text(text, encoding="utf-8", newline="")
            queued = {
                "voice_id": voice_id,
                "voice": "pocket-alba",
                "status": "queued",
                "status_url": f"/v1/voice/{voice_id}",
            }
            with self._state_lock:
                self._jobs[voice_id] = queued
            worker = threading.Thread(target=self._run_job, args=(voice_id,), daemon=True)
            self._worker_thread = worker
            worker.start()
            return dict(queued)
        except BaseException:
            self._generation_lock.release()
            raise

    def _run_job(self, voice_id: str) -> None:
        with self._state_lock:
            self._jobs[voice_id] = {**self._jobs[voice_id], "status": "generating"}
        try:
            result = self._generate(voice_id)
        except Exception:
            result = {"voice_id": voice_id, "voice": "pocket-alba", "status": "failed"}
        finally:
            with self._state_lock:
                self._process = None
            self._generation_lock.release()
        with self._state_lock:
            self._jobs[voice_id] = result

    def _generate(self, voice_id: str) -> dict[str, object]:
        folder = self.voice_root / voice_id
        command = [
            str(self.python), str(self.script), "--voice", "pocket-alba",
            "--text-file", str(folder / "script.txt"), "--output", str(folder / "response.wav"),
        ]
        offline_env = os.environ.copy()
        offline_env.update({
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
        })
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, env=offline_env)
            with self._state_lock:
                self._process = process
            process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            process.communicate()
            raise VoiceGenerationFailed("Local speech timed out") from exc
        except OSError as exc:
            raise VoiceGenerationFailed("Local speech could not start") from exc
        if process.returncode != 0:
            raise VoiceGenerationFailed("Local speech process failed")
        verified = self._verified_take(voice_id)
        if verified is None:
            raise VoiceGenerationFailed("Local speech receipt did not verify")
        return verified

    def _verified_take(self, voice_id: str) -> dict[str, object] | None:
        if not VOICE_ID.fullmatch(voice_id):
            return None
        folder = self.voice_root / voice_id
        wav_path = folder / "response.wav"
        receipt_path = folder / "response.json"
        if folder.is_symlink() or wav_path.is_symlink() or receipt_path.is_symlink():
            return None
        if not wav_path.is_file() or not receipt_path.is_file():
            return None
        try:
            if not 44 <= wav_path.stat().st_size <= MAX_WAV_BYTES:
                return None
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            digest = hashlib.sha256(wav_path.read_bytes()).hexdigest()
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(receipt, dict):
            return None
        if receipt.get("voice_id") != "pocket-alba" or receipt.get("sha256") != digest:
            return None
        return {
            "voice_id": voice_id,
            "voice": "pocket-alba",
            "status": "generated_pending_listening_review",
            "sha256": digest,
            "duration_seconds": receipt.get("duration_seconds"),
            "status_url": f"/v1/voice/{voice_id}",
            "audio_url": f"/v1/voice/{voice_id}/audio.wav",
        }

    def status(self, voice_id: str) -> dict[str, object] | None:
        if not VOICE_ID.fullmatch(voice_id):
            return None
        with self._state_lock:
            active = self._jobs.get(voice_id)
        if active is not None:
            return dict(active)
        folder = self.voice_root / voice_id
        if folder.is_symlink() or not (folder / "script.txt").is_file():
            return None
        return self._verified_take(voice_id) or {"voice_id": voice_id, "voice": "pocket-alba", "status": "interrupted"}

    def audio_path(self, voice_id: str) -> Path | None:
        result = self.status(voice_id)
        if result is None or result["status"] != "generated_pending_listening_review":
            return None
        folder = self.voice_root / voice_id
        path = folder / "response.wav"
        return path

    def close(self) -> None:
        self._closed = True
        with self._state_lock:
            process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5)
