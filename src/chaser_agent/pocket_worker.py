"""Private JSON-line worker for the approved, local Pocket Alba speech preset.

Run only by PocketAlbaVoice with a pinned Python environment. It has no socket,
provider route, microphone access, arbitrary output path, or model download.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

VOICE_ID = re.compile(r"^voice-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}$")


def emit(event: str, voice_id: str | None = None) -> None:
    message = {"event": event}
    if voice_id is not None:
        message["voice_id"] = voice_id
    print(json.dumps(message, separators=(",", ":")), flush=True)


def job_paths(output_root: Path, voice_id: str) -> tuple[Path, Path, Path]:
    """Resolve only a new, single-ID take inside the configured output root."""
    if not VOICE_ID.fullmatch(voice_id):
        raise ValueError("Invalid voice job ID")
    folder = output_root / voice_id
    script = folder / "script.txt"
    wav = folder / "response.wav"
    receipt = folder / "response.json"
    if folder.is_symlink() or script.is_symlink() or wav.is_symlink() or receipt.is_symlink():
        raise ValueError("Voice job path is a symlink")
    if not folder.is_dir() or not script.is_file() or wav.exists() or receipt.exists():
        raise ValueError("Voice job is missing or already has output")
    return script, wav, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--preset", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve(strict=True)
    if not args.config.is_file() or not args.preset.is_file():
        return 2

    emit("starting")
    import torch
    from pocket_tts import TTSModel
    from scipy.io.wavfile import write
    emit("libraries_loaded")

    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    model = TTSModel.load_model(config=str(args.config))
    model.has_voice_cloning = False
    emit("model_loaded")
    state = model.get_state_for_audio_prompt(args.preset)
    emit("ready")

    for line in sys.stdin:
        voice_id: str | None = None
        try:
            request = json.loads(line)
            voice_id = request.get("voice_id") if isinstance(request, dict) else None
            if not isinstance(voice_id, str):
                emit("error")
                continue
            try:
                script, wav, receipt = job_paths(output_root, voice_id)
            except ValueError:
                emit("error", voice_id)
                continue
            text = script.read_text(encoding="utf-8-sig").strip()
            if not 1 <= len(text) <= 500:
                emit("error", voice_id)
                continue
            started = time.monotonic()
            torch.manual_seed(20260906)
            audio = model.generate_audio(state, text).detach().cpu().numpy()
            sample_rate = model.sample_rate
            write(str(wav), sample_rate, audio)
            digest = hashlib.sha256(wav.read_bytes()).hexdigest()
            metadata = {
                "library_id": "chaseos-local-speech-production",
                "voice_id": "pocket-alba",
                "text": text,
                "seed": 20260906,
                "method": "published preset / public non-cloning weights; warm local worker",
                "output": str(wav.resolve()),
                "sha256": digest,
                "sample_rate": sample_rate,
                "duration_seconds": len(audio) / sample_rate,
                "generation_seconds": round(time.monotonic() - started, 2),
                "listening_acceptance": "new take requires review",
                "source_library": str(args.library_root.resolve()),
                "attribution": str(args.library_root.resolve() / "receipts" / "Attribution.md"),
            }
            receipt.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            emit("done", voice_id)
        except (OSError, ValueError, TypeError, RuntimeError):
            emit("error", voice_id if isinstance(voice_id, str) else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
