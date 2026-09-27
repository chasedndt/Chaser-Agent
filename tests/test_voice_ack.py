import io
import json
import sys
import threading
import types
from pathlib import Path

import pytest

from chaser_agent.voice_ack import ACK_TEXT, speak_ack, speak_status_reply


def test_ack_requires_local_token_and_never_accepts_bad_port(tmp_path):
    with pytest.raises(ValueError):
        speak_ack(data_dir=tmp_path, port=0)
    with pytest.raises(ValueError):
        speak_ack(data_dir=tmp_path)


def test_ack_sends_only_fixed_public_text_and_plays_verified_route(monkeypatch, tmp_path: Path):
    (tmp_path / "control-token").write_text("a" * 64, encoding="ascii")
    monkeypatch.setattr("chaser_agent.voice_ack.read_private_control_token", lambda _path: "a" * 64)
    voice_id = "voice-20260927T120000000000Z-abcdef123456"
    status_path = f"/v1/voice/{voice_id}"
    seen = []

    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else request
        seen.append((url, getattr(request, "data", None)))
        if url.endswith("/v1/health"):
            payload = {"voice_runtime": "ready"}
        elif url.endswith("/v1/voice/replies"):
            payload = {"status_url": status_path}
        elif url.endswith("/audio.wav"):
            return io.BytesIO(b"RIFF" + b"\x00" * 64)
        else:
            payload = {"status": "generated_pending_listening_review", "audio_url": status_path + "/audio.wav", "voice_id": voice_id}
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    played = []
    monkeypatch.setattr("chaser_agent.voice_ack.urlopen", fake_urlopen)
    monkeypatch.setitem(sys.modules, "winsound", types.SimpleNamespace(
        SND_MEMORY=4, PlaySound=lambda audio, flags: played.append((audio, flags)),
    ))
    assert speak_ack(data_dir=tmp_path) == voice_id
    posted = json.loads(next(body for url, body in seen if url.endswith("/v1/voice/replies")))
    assert posted == {"text": ACK_TEXT, "privacy_class": "public_toy"}
    assert not any(url.endswith("/cancel") for url, _ in seen)
    assert len(played) == 1 and played[0][0].startswith(b"RIFF")


def test_spoken_status_queries_hud_read_only_and_never_posts_transcript(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("chaser_agent.voice_ack.read_private_control_token", lambda _path: "a" * 64)
    voice_id = "voice-20260927T120000000000Z-abcdef123456"
    status_path = f"/v1/voice/{voice_id}"
    seen = []

    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else request
        body = getattr(request, "data", None)
        seen.append((url, body))
        if url.endswith("/v1/health"):
            payload = {"service": "chaser-agent", "status": "ready", "bind": "127.0.0.1",
                       "port": 8765, "mode": "review_with_local_voice", "voice_runtime": "ready"}
        elif url.endswith("/v1/hud/current"):
            payload = {"status": "inactive", "action": "private content"}
        elif url.endswith("/v1/voice/replies"):
            payload = {"status_url": status_path}
        elif url.endswith("/audio.wav"):
            return io.BytesIO(b"RIFF" + b"\x00" * 64)
        else:
            payload = {"status": "generated_pending_listening_review",
                       "audio_url": status_path + "/audio.wav", "voice_id": voice_id}
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    played = []
    monkeypatch.setattr("chaser_agent.voice_ack.urlopen", fake_urlopen)
    monkeypatch.setitem(sys.modules, "winsound", types.SimpleNamespace(
        SND_MEMORY=4, PlaySound=lambda audio, flags: played.append(audio),
    ))
    assert speak_status_reply(data_dir=tmp_path, transcript="Stop the computer") is None
    assert not seen
    reply, returned_id = speak_status_reply(data_dir=tmp_path, transcript="What's your status?")
    assert returned_id == voice_id
    assert reply == "The local review service is ready on port 8765. No computer-use executor is connected."
    assert [url for url, _ in seen if "/v1/hud/controls" in url] == []
    posted = json.loads(next(body for url, body in seen if url.endswith("/v1/voice/replies")))
    assert posted == {"text": reply, "privacy_class": "public_toy"}
    assert "What's your status" not in json.dumps(posted)
    assert len(played) == 1


def test_cancelled_status_speech_never_posts_audio_job(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("chaser_agent.voice_ack.read_private_control_token", lambda _path: "a" * 64)
    cancel = threading.Event()
    seen = []

    def fake_urlopen(request, timeout):
        url = request.full_url if hasattr(request, "full_url") else request
        seen.append(url)
        if url.endswith("/v1/health"):
            payload = {"service": "chaser-agent", "status": "ready", "bind": "127.0.0.1",
                       "port": 8765, "mode": "review_with_local_voice", "voice_runtime": "ready"}
        else:
            cancel.set()
            payload = {"status": "inactive"}
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("chaser_agent.voice_ack.urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="cancelled"):
        speak_status_reply(data_dir=tmp_path, transcript="What's your status?", cancel_event=cancel)
    assert not any(url.endswith("/v1/voice/replies") for url in seen)


def test_cancel_after_job_post_requests_exact_owned_take_stop(monkeypatch):
    from chaser_agent.voice_ack import _play_public_text

    cancel = threading.Event()
    voice_id = "voice-20260927T120000000000Z-abcdef123456"
    path = f"/v1/voice/{voice_id}"
    seen = []

    def fake_urlopen(request, timeout):
        url = request.full_url
        seen.append((url, getattr(request, "data", None)))
        if url.endswith("/v1/voice/replies"):
            payload = {"status_url": path}
        elif url.endswith(path + "/cancel"):
            payload = {"status": "cancelling"}
        else:
            cancel.set()
            payload = {"status": "generating"}
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("chaser_agent.voice_ack.urlopen", fake_urlopen)
    monkeypatch.setattr("chaser_agent.voice_ack.time.sleep", lambda _seconds: None)
    with pytest.raises(RuntimeError, match="cancelled"):
        _play_public_text(base="http://127.0.0.1:8765", token="a" * 64,
                          text="Public toy reply", timeout=5, cancel_event=cancel)
    assert [url for url, _ in seen if url.endswith("/cancel")] == [
        f"http://127.0.0.1:8765{path}/cancel",
    ]
    assert json.loads(seen[-1][1]) == {}


def test_poll_failure_after_job_post_still_requests_cancel(monkeypatch):
    from chaser_agent.voice_ack import _play_public_text

    voice_id = "voice-20260927T120000000000Z-abcdef123456"
    path = f"/v1/voice/{voice_id}"
    seen = []

    def fake_urlopen(request, timeout):
        url = request.full_url
        seen.append(url)
        if url.endswith("/v1/voice/replies"):
            return io.BytesIO(json.dumps({"status_url": path}).encode("utf-8"))
        if url.endswith("/cancel"):
            return io.BytesIO(b'{}')
        raise OSError("local poll failed")

    monkeypatch.setattr("chaser_agent.voice_ack.urlopen", fake_urlopen)
    with pytest.raises(OSError, match="poll failed"):
        _play_public_text(base="http://127.0.0.1:8765", token="a" * 64,
                          text="Public toy reply", timeout=5)
    assert seen[-1] == f"http://127.0.0.1:8765{path}/cancel"
