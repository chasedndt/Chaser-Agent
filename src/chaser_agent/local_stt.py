"""Opt-in, offline speech input. Transcripts are untrusted drafts, never commands."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import wave
from pathlib import Path

SAMPLE_RATE = 16_000
MAX_SECONDS = 12
MIN_SECONDS = 0.5
MODEL_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
MODEL_REPO = "Systran/faster-whisper-tiny.en"
MODEL_REVISION = "0d3d19a32d3338f10357c0889762bd8d64bbdeba"


def verify_local_model(model_dir: Path) -> dict[str, object]:
    if model_dir.is_symlink() or not model_dir.is_dir():
        raise ValueError("A real local STT model directory is required")
    manifest_path = model_dir / "stt-model.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("The local STT model receipt is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or manifest.get("schema_version") != 1
            or manifest.get("source_repo") != MODEL_REPO
            or manifest.get("revision") != MODEL_REVISION
            or not isinstance(manifest.get("files"), dict)
            or set(manifest["files"]) != set(MODEL_FILES)):
        raise ValueError("The local STT model receipt is invalid")
    for name in MODEL_FILES:
        path = model_dir / name
        expected = manifest["files"][name]
        if (path.is_symlink() or not path.is_file() or not isinstance(expected, str)
                or len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected)):
            raise ValueError("The local STT model file or hash is invalid")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != expected:
            raise ValueError("The local STT model file changed after setup")
    return manifest


def validate_pcm(pcm: bytes) -> float:
    if not isinstance(pcm, bytes) or len(pcm) % 2:
        raise ValueError("16-bit mono PCM is required")
    duration = len(pcm) / (SAMPLE_RATE * 2)
    if not MIN_SECONDS <= duration <= MAX_SECONDS:
        raise ValueError("Speech input must be 0.5–12 seconds")
    return duration


def read_pcm_wav(path: Path) -> bytes:
    """Read a bounded local test take without allowing a model to decode it."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("A small local WAV file is required")
    try:
        with wave.open(str(path), "rb") as source:
            if (source.getnchannels() != 1 or source.getsampwidth() != 2
                    or source.getframerate() != SAMPLE_RATE
                    or source.getnframes() > MAX_SECONDS * SAMPLE_RATE):
                raise ValueError("WAV must be 16 kHz, mono, 16-bit PCM and at most 12 seconds")
            pcm = source.readframes(source.getnframes())
    except (wave.Error, EOFError) as exc:
        raise ValueError("Invalid PCM WAV file") from exc
    validate_pcm(pcm)
    return pcm


class OfflineTranscriber:
    def __init__(self, model_dir: Path, *, model_factory=None):
        self.model_dir = model_dir.resolve(strict=True)
        self.manifest = verify_local_model(model_dir)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
        if model_factory is None:
            from faster_whisper import WhisperModel

            model_factory = WhisperModel
        self.model = model_factory(str(self.model_dir), device="cpu", compute_type="int8", local_files_only=True)

    def transcribe(self, pcm: bytes) -> dict[str, object]:
        duration = validate_pcm(pcm)
        import numpy as np

        audio = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(audio * audio)))
        if rms < 0.003:
            return {"status": "no_speech", "text": "", "duration_seconds": duration}
        segments, info = self.model.transcribe(
            audio, language="en", beam_size=1, condition_on_previous_text=False,
            vad_filter=False,
        )
        text = " ".join(part.text.strip() for part in segments).strip()
        if len(text) > 2000:
            raise ValueError("Transcript exceeds the review limit")
        return {
            "status": "draft_unverified" if text else "no_speech",
            "text": text,
            "language": info.language,
            "duration_seconds": duration,
            "audio_sha256": hashlib.sha256(pcm).hexdigest(),
            "model_revision": MODEL_REVISION,
            "authority": "transcript_only_no_dispatch",
        }


class CaptureCancelled(RuntimeError):
    """An explicit operator cancellation discarded an unfinished take."""


def record_once(seconds: float, *, device: int | None = None,
                cancel_event: threading.Event | None = None) -> bytes:
    """Open the microphone only during one explicit, bounded capture."""
    if not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise ValueError("Capture must be 0.5–12 seconds")
    if cancel_event is not None and cancel_event.is_set():
        raise CaptureCancelled("Microphone take cancelled before opening")
    import sounddevice as sd

    total_frames = int(seconds * SAMPLE_RATE)
    chunks: list[bytes] = []
    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", device=device) as stream:
        remaining = total_frames
        while remaining:
            if cancel_event is not None and cancel_event.is_set():
                raise CaptureCancelled("Microphone take cancelled")
            frames = min(1600, remaining)
            chunk, overflowed = stream.read(frames)
            if cancel_event is not None and cancel_event.is_set():
                raise CaptureCancelled("Microphone take cancelled")
            if overflowed:
                raise RuntimeError("Microphone overflowed; the capture was discarded")
            chunks.append(bytes(chunk))
            remaining -= frames
    pcm = b"".join(chunks)
    validate_pcm(pcm)
    return pcm
