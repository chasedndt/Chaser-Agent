"""Offline speech-input boundary tests; optional model runtime is not needed."""

import hashlib
import argparse
import json
import math
import struct
import sys
import types
import wave
from pathlib import Path

import pytest

from chaser_agent.local_stt import (
    MODEL_FILES, MODEL_REPO, MODEL_REVISION, OfflineTranscriber,
    read_pcm_wav, record_once, validate_pcm, verify_local_model,
)
from chaser_agent.cli import run_voice_mode_command


@pytest.fixture
def model_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "model"
    folder.mkdir()
    hashes = {}
    for name in MODEL_FILES:
        payload = name.encode("ascii")
        (folder / name).write_bytes(payload)
        hashes[name] = hashlib.sha256(payload).hexdigest()
    (folder / "stt-model.json").write_text(json.dumps({
        "schema_version": 1, "source_repo": MODEL_REPO,
        "revision": MODEL_REVISION, "files": hashes,
    }), encoding="utf-8")
    return folder


def test_pinned_model_receipt_detects_changes(model_dir):
    assert verify_local_model(model_dir)["revision"] == MODEL_REVISION
    (model_dir / "model.bin").write_bytes(b"different")
    with pytest.raises(ValueError, match="changed"):
        verify_local_model(model_dir)


def test_pcm_bounds_and_test_wav_format(tmp_path):
    pcm = b"\x00\x00" * 16_000
    assert validate_pcm(pcm) == 1.0
    with pytest.raises(ValueError):
        validate_pcm(b"\x00")
    with pytest.raises(ValueError):
        validate_pcm(pcm * 13)
    path = tmp_path / "toy.wav"
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16_000)
        output.writeframes(pcm)
    assert read_pcm_wav(path) == pcm


def test_microphone_opens_only_for_bounded_capture(monkeypatch):
    with pytest.raises(ValueError):
        record_once(30)

    class FakeStream:
        def __init__(self, **kwargs):
            assert kwargs["samplerate"] == 16_000 and kwargs["channels"] == 1
            self.opened = False

        def __enter__(self):
            self.opened = True
            return self

        def __exit__(self, *_args):
            self.opened = False

        def read(self, frames):
            assert self.opened
            return b"\x00\x00" * frames, False

    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(RawInputStream=FakeStream))
    assert len(record_once(0.5)) == 16_000


def test_transcription_is_a_draft_and_never_dispatches(model_dir):
    np = pytest.importorskip("numpy")
    calls = []

    class FakeModel:
        def transcribe(self, audio, **kwargs):
            assert isinstance(audio, np.ndarray)
            calls.append(kwargs)
            return [types.SimpleNamespace(text="  A toy request. ")], types.SimpleNamespace(language="en")

    def factory(path, **kwargs):
        assert path == str(model_dir.resolve())
        assert kwargs["local_files_only"] is True
        return FakeModel()

    engine = OfflineTranscriber(model_dir, model_factory=factory)
    pcm = b"".join(struct.pack("<h", int(8000 * math.sin(i / 20))) for i in range(16_000))
    result = engine.transcribe(pcm)
    assert result["status"] == "draft_unverified"
    assert result["text"] == "A toy request."
    assert result["authority"] == "transcript_only_no_dispatch"
    assert calls[0]["language"] == "en"
    assert engine.transcribe(b"\x00\x00" * 16_000)["status"] == "no_speech"
    assert len(calls) == 1


def test_voice_mode_rejects_bad_capture_or_ack_config_before_model_load(capsys):
    args = argparse.Namespace(model_dir="missing", sample_wav=None, seconds=30, speak_ack=False,
                              data_dir=None, port=8765, device=None)
    assert run_voice_mode_command(args) == 2
    assert "0.5–12" in capsys.readouterr().err
    args.seconds = 5
    args.speak_ack = True
    assert run_voice_mode_command(args) == 2
    assert "requires --data-dir" in capsys.readouterr().err
    args.speak_ack = False
    args.speak_status = True
    assert run_voice_mode_command(args) == 2
    assert "requires --data-dir" in capsys.readouterr().err


def test_voice_mode_routes_only_status_draft_to_read_only_reply(monkeypatch, tmp_path, capsys):
    calls = []

    class FakeTranscriber:
        def __init__(self, _model_dir):
            pass

        def transcribe(self, _pcm):
            return {"status": "draft_unverified", "text": "What's your status?",
                    "authority": "transcript_only_no_dispatch"}

    monkeypatch.setattr("chaser_agent.local_stt.OfflineTranscriber", FakeTranscriber)
    monkeypatch.setattr("chaser_agent.local_stt.read_pcm_wav", lambda _path: b"toy pcm")

    def fake_reply(**kwargs):
        calls.append(kwargs)
        return "No computer-use executor is connected.", "toy-voice-id"

    monkeypatch.setattr("chaser_agent.voice_ack.speak_status_reply", fake_reply)
    args = argparse.Namespace(model_dir=str(tmp_path), sample_wav=str(tmp_path / "toy.wav"),
                              seconds=5, speak_ack=False, speak_status=True,
                              data_dir=str(tmp_path / "runtime"), port=8765, device=None)
    assert run_voice_mode_command(args) == 0
    assert calls[0]["transcript"] == "What's your status?"
    assert "Read-only local status reply played" in capsys.readouterr().out
