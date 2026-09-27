"""Cancellable output uses bounded PCM chunks without opening an input device."""

import io
import struct
import sys
import threading
import types
import wave

import pytest

from chaser_agent.local_audio import PlaybackCancelled, play_local_wav


def pcm_wav(*, width=2, channels=1, rate=16_000, frames=3_200):
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(width)
        writer.setframerate(rate)
        writer.writeframes(b"\x00" * (frames * channels * width))
    return output.getvalue()


def float_wav(*, value=0.25, rate=24_000, frames=4_800):
    payload = struct.pack(f"<{frames}f", *([value] * frames))
    fmt = struct.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"fact" + struct.pack("<I", 4) + struct.pack("<I", frames)
    chunks += b"data" + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks


def test_cancellable_playback_uses_output_only_stream_and_short_chunks(monkeypatch):
    created = []

    class FakeOutput:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.chunks = []
            self.started = self.stopped = self.aborted = self.closed = False
            created.append(self)

        def start(self):
            self.started = True

        def write(self, chunk):
            self.chunks.append(bytes(chunk))

        def stop(self):
            self.stopped = True

        def abort(self):
            self.aborted = True

        def close(self):
            self.closed = True

    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(RawOutputStream=FakeOutput))
    play_local_wav(pcm_wav(), cancel_event=threading.Event())
    stream = created[0]
    assert stream.kwargs == {"samplerate": 16_000, "channels": 1, "dtype": "int16"}
    assert stream.started and stream.stopped and stream.closed and not stream.aborted
    assert len(stream.chunks) == 4
    assert all(len(chunk) <= 1_600 for chunk in stream.chunks)


def test_cancel_during_playback_aborts_pending_output(monkeypatch):
    cancel = threading.Event()
    created = []

    class FakeOutput:
        def __init__(self, **_kwargs):
            self.writes = 0
            self.aborted = self.closed = self.stopped = False
            created.append(self)

        def start(self):
            pass

        def write(self, _chunk):
            self.writes += 1
            cancel.set()

        def stop(self):
            self.stopped = True

        def abort(self):
            self.aborted = True

        def close(self):
            self.closed = True

    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(RawOutputStream=FakeOutput))
    with pytest.raises(PlaybackCancelled):
        play_local_wav(pcm_wav(), cancel_event=cancel)
    assert created[0].writes == 1
    assert created[0].aborted and created[0].closed and not created[0].stopped


def test_float32_wav_from_local_speech_uses_bounded_output_chunks(monkeypatch):
    created = []

    class FakeOutput:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.chunks = []
            created.append(self)

        def start(self):
            pass

        def write(self, chunk):
            self.chunks.append(bytes(chunk))

        def stop(self):
            pass

        def close(self):
            pass

    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(RawOutputStream=FakeOutput))
    play_local_wav(float_wav(), cancel_event=threading.Event())
    assert created[0].kwargs == {"samplerate": 24_000, "channels": 1, "dtype": "float32"}
    assert len(created[0].chunks) == 4
    assert all(len(chunk) <= 4_800 for chunk in created[0].chunks)


def test_unsafe_float32_never_opens_output(monkeypatch):
    created = []
    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(
        RawOutputStream=lambda **kwargs: created.append(kwargs),
    ))
    for value in (float("nan"), 1.5):
        with pytest.raises(RuntimeError, match="unsafe floating-point audio"):
            play_local_wav(float_wav(value=value, frames=1), cancel_event=threading.Event())
    assert created == []


def test_pre_cancel_and_invalid_pcm_never_open_output(monkeypatch):
    created = []
    monkeypatch.setitem(sys.modules, "sounddevice", types.SimpleNamespace(
        RawOutputStream=lambda **kwargs: created.append(kwargs),
    ))
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(PlaybackCancelled):
        play_local_wav(pcm_wav(), cancel_event=cancel)
    with pytest.raises(RuntimeError, match="invalid WAV"):
        play_local_wav(b"RIFF", cancel_event=threading.Event())
    with pytest.raises(RuntimeError, match="unsupported PCM"):
        play_local_wav(pcm_wav(width=1), cancel_event=threading.Event())
    assert created == []


def test_cancellable_playback_fails_closed_without_optional_output_library(monkeypatch):
    monkeypatch.setitem(sys.modules, "sounddevice", None)
    with pytest.raises(RuntimeError, match="sounddevice"):
        play_local_wav(pcm_wav(), cancel_event=threading.Event())
