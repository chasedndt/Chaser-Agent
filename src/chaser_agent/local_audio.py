"""Local WAV playback, with an output-only cancellable path for the HUD."""

from __future__ import annotations

import math
import struct
import sys
import threading

MAX_PLAYBACK_SECONDS = 60
PLAYBACK_CHUNK_SECONDS = 0.05
MAX_LOCAL_AUDIO_BYTES = 10_000_000


class PlaybackCancelled(RuntimeError):
    pass


def _wav_samples(audio: bytes) -> tuple[int, int, str, int, memoryview]:
    """Accept only bounded little-endian PCM16 or IEEE-float32 RIFF/WAVE."""
    if (sys.byteorder != "little" or not 44 <= len(audio) <= MAX_LOCAL_AUDIO_BYTES
            or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE"):
        raise RuntimeError("Local voice returned an invalid WAV")
    riff_end = struct.unpack_from("<I", audio, 4)[0] + 8
    if riff_end != len(audio):
        raise RuntimeError("Local voice returned an invalid WAV")
    position = 12
    fmt = None
    samples = None
    while position + 8 <= riff_end:
        chunk_type = audio[position:position + 4]
        size = struct.unpack_from("<I", audio, position + 4)[0]
        start = position + 8
        end = start + size
        if end > riff_end:
            raise RuntimeError("Local voice returned an invalid WAV")
        if chunk_type == b"fmt ":
            if fmt is not None or size < 16:
                raise RuntimeError("Local voice returned an invalid WAV")
            fmt = struct.unpack_from("<HHIIHH", audio, start)
        elif chunk_type == b"data":
            if samples is not None:
                raise RuntimeError("Local voice returned an invalid WAV")
            samples = memoryview(audio)[start:end]
        position = end + (size & 1)
    if position != riff_end or fmt is None or samples is None:
        raise RuntimeError("Local voice returned an invalid WAV")
    format_code, channels, rate, byte_rate, frame_bytes, bits = fmt
    if format_code == 1 and bits == 16:
        dtype = "int16"
    elif format_code == 3 and bits == 32:
        dtype = "float32"
    else:
        raise RuntimeError("Local voice returned an unsupported PCM WAV")
    if (channels not in {1, 2} or not 8_000 <= rate <= 48_000
            or frame_bytes != channels * bits // 8 or byte_rate != rate * frame_bytes
            or len(samples) == 0 or len(samples) % frame_bytes
            or len(samples) // frame_bytes > rate * MAX_PLAYBACK_SECONDS):
        raise RuntimeError("Local voice returned an unsupported PCM WAV")
    if dtype == "float32" and any(not math.isfinite(value) or abs(value) > 1.0
                                  for (value,) in struct.iter_unpack("<f", samples)):
        raise RuntimeError("Local voice returned unsafe floating-point audio")
    return channels, rate, dtype, frame_bytes, samples


def play_local_wav(audio: bytes, *, cancel_event: threading.Event | None = None) -> None:
    """Play one local take; a HUD stop aborts pending output buffers."""
    if cancel_event is None:
        import winsound

        winsound.PlaySound(audio, winsound.SND_MEMORY)
        return
    if cancel_event.is_set():
        raise PlaybackCancelled("Local playback cancelled before opening output")
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Cancellable audio output requires the optional sounddevice environment") from exc
    channels, rate, dtype, frame_bytes, samples = _wav_samples(audio)
    bytes_per_chunk = max(1, round(rate * PLAYBACK_CHUNK_SECONDS)) * frame_bytes
    stream = None
    try:
        stream = sd.RawOutputStream(samplerate=rate, channels=channels, dtype=dtype)
        stream.start()
        for offset in range(0, len(samples), bytes_per_chunk):
            if cancel_event.is_set():
                raise PlaybackCancelled("Local playback cancelled")
            stream.write(samples[offset:offset + bytes_per_chunk])
        if cancel_event.is_set():
            raise PlaybackCancelled("Local playback cancelled")
        stream.stop()
    except PlaybackCancelled:
        if stream is not None:
            try:
                stream.abort()
            except Exception:
                pass
        raise
    except Exception as exc:
        if stream is not None:
            try:
                stream.abort()
            except Exception:
                pass
        raise RuntimeError("Local audio output failed") from exc
    finally:
        if stream is not None:
            try:
                stream.close()
            except Exception:
                pass
