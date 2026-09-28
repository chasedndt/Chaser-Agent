"""Optional, offline Pocket Alba response adapter for a local Chaser instance.

The speech library is operator-supplied at startup. HTTP callers cannot select
an executable, model, voice, output path, or provider. A generated take still
requires listening review; this module does not make it canonical media.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import secrets
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

VOICE_ID = re.compile(r"^voice-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")
MAX_SPEECH_CHARS = 500
MAX_WAV_BYTES = 20_000_000
TERMINAL_VOICE_STATUSES = frozenset({"generated_pending_listening_review", "failed", "interrupted", "cancelled"})


class VoiceBusy(RuntimeError):
    pass


class VoiceGenerationFailed(RuntimeError):
    pass


def stop_owned_process(process: subprocess.Popen[str]) -> None:
    """Stop this adapter's exact child tree, including Windows venv launchers."""
    if process.poll() is not None:
        return
    if os.name == "nt" and isinstance(getattr(process, "pid", None), int):
        try:
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    if process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


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
        voices = manifest.get("voices", [])
        if not isinstance(voices, list):
            raise ValueError("The local voice manifest is invalid")
        voice_record = next(
            (voice for voice in voices if isinstance(voice, dict) and voice.get("id") == "pocket-alba"), None
        )
        if not isinstance(voice_record, dict) or not isinstance(voice_record.get("production_root"), str):
            raise ValueError("The approved local voice production root is missing")
        self.production_root = Path(voice_record["production_root"]).resolve(strict=True)
        if not self.production_root.is_dir():
            raise ValueError("The approved local voice production root is not a directory")
        runtime = manifest.get("runtime_paths", {})
        for key in ("pocket_python", "pocket_config", "pocket_voices"):
            if not isinstance(runtime.get(key), str) or not Path(runtime[key]).exists():
                raise ValueError(f"The local voice runtime is missing {key}")
        if not (Path(runtime["pocket_voices"]) / "alba.safetensors").is_file():
            raise ValueError("The local Pocket Alba preset is missing")
        self.config = Path(runtime["pocket_config"])
        self.preset = Path(runtime["pocket_voices"]) / "alba.safetensors"
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
        self._active_voice_id: str | None = None
        self._cancelled: set[str] = set()
        self._closed = False

    @staticmethod
    def _cancelled_result(voice_id: str) -> dict[str, object]:
        return {"voice_id": voice_id, "voice": "pocket-alba", "status": "cancelled"}

    def _is_cancelled(self, voice_id: str) -> bool:
        with self._state_lock:
            return voice_id in self._cancelled

    @staticmethod
    def _stop_cancelled_process(process: subprocess.Popen[str]) -> None:
        try:
            stop_owned_process(process)
        except Exception:
            # The take remains cancelled and inaccessible even if the exact
            # owned child is slow or refuses to stop before its timeout.
            pass

    def cancel(self, voice_id: str) -> dict[str, object] | None:
        """Cancel one known take; never kill a process not owned by this adapter."""
        if not VOICE_ID.fullmatch(voice_id):
            return None
        with self._state_lock:
            current = self._jobs.get(voice_id)
            if current is None:
                return None
            if current["status"] in TERMINAL_VOICE_STATUSES or current["status"] == "cancelling":
                return dict(current)
            marker = self.voice_root / voice_id / "cancelled.json"
            if marker.is_symlink():
                raise VoiceGenerationFailed("Local cancellation marker is unsafe")
            try:
                descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    json.dump(self._cancelled_result(voice_id), stream)
            except FileExistsError:
                if not marker.is_file() or marker.is_symlink():
                    raise VoiceGenerationFailed("Local cancellation marker is unsafe")
            except OSError as exc:
                raise VoiceGenerationFailed("Local cancellation marker could not be written") from exc
            self._cancelled.add(voice_id)
            self._jobs[voice_id] = {"voice_id": voice_id, "voice": "pocket-alba", "status": "cancelling"}
            process = self._process if self._active_voice_id == voice_id else None
            result = dict(self._jobs[voice_id])
        if process is not None and process.poll() is None:
            threading.Thread(target=self._stop_cancelled_process, args=(process,), daemon=True).start()
        return result

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
            cancelled_before_start = voice_id in self._cancelled
            if not cancelled_before_start:
                self._jobs[voice_id] = {**self._jobs[voice_id], "status": "generating"}
                self._active_voice_id = voice_id
        try:
            result = self._cancelled_result(voice_id) if cancelled_before_start else self._generate(voice_id)
        except Exception:
            result = {"voice_id": voice_id, "voice": "pocket-alba", "status": "failed"}
        finally:
            self._after_job()
            with self._state_lock:
                if voice_id in self._cancelled:
                    result = self._cancelled_result(voice_id)
                    self._cancelled.discard(voice_id)
                self._jobs[voice_id] = result
                if self._active_voice_id == voice_id:
                    self._active_voice_id = None
            self._generation_lock.release()

    def _after_job(self) -> None:
        with self._state_lock:
            self._process = None

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
            if self._is_cancelled(voice_id):
                raise VoiceGenerationFailed("Local speech take cancelled")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, env=offline_env)
            with self._state_lock:
                self._process = process
            if self._is_cancelled(voice_id):
                stop_owned_process(process)
                raise VoiceGenerationFailed("Local speech take cancelled")
            process.communicate(timeout=300)
        except subprocess.TimeoutExpired as exc:
            stop_owned_process(process)
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
        marker = folder / "cancelled.json"
        if marker.is_symlink():
            return {"voice_id": voice_id, "voice": "pocket-alba", "status": "interrupted"}
        if marker.is_file():
            return self._cancelled_result(voice_id)
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
            stop_owned_process(process)
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5)


class WarmPocketAlbaVoice(PocketAlbaVoice):
    """Keep the approved model loaded across replies in one private process."""

    def __init__(self, *, library_root: Path, data_dir: Path):
        super().__init__(library_root=library_root, data_dir=data_dir)
        self.worker_script = Path(__file__).with_name("pocket_worker.py")
        if not self.worker_script.is_file():
            raise ValueError("The local warm speech worker is missing")
        self._events: queue.Queue[dict[str, object] | None] | None = None
        self._reader_thread: threading.Thread | None = None
        self._ready = False
        self._prewarm_failed = False
        self._startup_started: float | None = None
        self._startup_timings: dict[str, float] = {}

    def startup_diagnostics(self) -> dict[str, object]:
        """Content-free timings for the latest worker; never report stale readiness."""
        with self._state_lock:
            return {"milestones_seconds": dict(self._startup_timings)}

    def prewarm(self) -> None:
        """Load the model in the background before the first voice reply."""
        if not self._generation_lock.acquire(blocking=False):
            return
        self._prewarm_failed = False
        worker = threading.Thread(target=self._prewarm_worker, daemon=True)
        self._worker_thread = worker
        worker.start()

    def _prewarm_worker(self) -> None:
        try:
            self._start_worker()
        except Exception:
            self._prewarm_failed = True
            self._reset_worker()
        finally:
            self._generation_lock.release()

    def runtime_state(self) -> str:
        if self._closed:
            return "closed"
        with self._state_lock:
            process = self._process
        if self._ready and process is not None and process.poll() is None:
            return "busy" if self._generation_lock.locked() else "ready"
        if self._generation_lock.locked():
            return "starting"
        return "failed" if self._prewarm_failed else "cold"

    def _after_job(self) -> None:
        # The model process remains alive and ready for the next bounded job.
        return

    @staticmethod
    def _read_events(process: subprocess.Popen[str], events: queue.Queue[dict[str, object] | None]) -> None:
        assert process.stdout is not None
        for line in process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("event") in {
                "starting", "libraries_loaded", "model_loaded", "ready", "done", "error"
            }:
                events.put(event)
        events.put(None)

    def _await_event(self, *, timeout: int) -> dict[str, object]:
        assert self._events is not None
        deadline = time.monotonic() + timeout
        while True:
            try:
                event = self._events.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise VoiceGenerationFailed("Local speech worker timed out") from exc
            if event is None:
                raise VoiceGenerationFailed("Local speech worker exited")
            if event.get("event") in {"starting", "libraries_loaded", "model_loaded", "ready"}:
                with self._state_lock:
                    if self._startup_started is not None:
                        self._startup_timings.setdefault(
                            event["event"], round(time.monotonic() - self._startup_started, 3)
                        )
            if event.get("event") in {"starting", "libraries_loaded", "model_loaded"}:
                with self._state_lock:
                    voice_id = self._active_voice_id
                    if voice_id is not None and voice_id in self._jobs:
                        self._jobs[voice_id] = {**self._jobs[voice_id], "stage": event["event"]}
                continue
            return event

    def _start_worker(self) -> subprocess.Popen[str]:
        with self._state_lock:
            process = self._process
        if process is not None and process.poll() is None and self._ready:
            return process
        if self._closed:
            raise VoiceGenerationFailed("Local speech adapter is closed")
        self._ready = False
        with self._state_lock:
            self._startup_started = time.monotonic()
            self._startup_timings = {}
        offline_env = os.environ.copy()
        offline_env.update({
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HOME": str(self.production_root / "cache" / "huggingface"),
            "TORCH_HOME": str(self.production_root / "cache" / "torch"),
            "OMP_NUM_THREADS": "2",
        })
        command = [
            str(self.python), "-u", str(self.worker_script),
            "--config", str(self.config), "--preset", str(self.preset),
            "--library-root", str(self.library_root), "--output-root", str(self.voice_root),
        ]
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1, env=offline_env,
            )
        except OSError as exc:
            raise VoiceGenerationFailed("Local speech worker could not start") from exc
        with self._state_lock:
            self._process = process
        self._events = queue.Queue()
        self._reader_thread = threading.Thread(
            target=self._read_events, args=(process, self._events), daemon=True
        )
        self._reader_thread.start()
        event = self._await_event(timeout=240)
        if event.get("event") != "ready":
            raise VoiceGenerationFailed("Local speech worker did not become ready")
        self._ready = True
        return process

    def _generate(self, voice_id: str) -> dict[str, object]:
        try:
            process = self._start_worker()
            if self._is_cancelled(voice_id):
                raise VoiceGenerationFailed("Local speech take cancelled")
            if process.stdin is None:
                raise VoiceGenerationFailed("Local speech input pipe is unavailable")
            process.stdin.write(json.dumps({"voice_id": voice_id}) + "\n")
            process.stdin.flush()
            event = self._await_event(timeout=120)
            if event.get("event") != "done" or event.get("voice_id") != voice_id:
                raise VoiceGenerationFailed("Local speech worker did not complete the requested take")
            verified = self._verified_take(voice_id)
            if verified is None:
                raise VoiceGenerationFailed("Local speech receipt did not verify")
            return verified
        except (VoiceGenerationFailed, OSError):
            self._reset_worker()
            raise

    def _reset_worker(self) -> None:
        self._ready = False
        with self._state_lock:
            process = self._process
            self._process = None
        if process is not None and process.poll() is None:
            stop_owned_process(process)

    def close(self) -> None:
        super().close()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=5)
