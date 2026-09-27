import io
import json
import sys
import types
from pathlib import Path

import pytest

from chaser_agent.voice_ack import ACK_TEXT, speak_ack


def test_ack_requires_local_token_and_never_accepts_bad_port(tmp_path):
    with pytest.raises(ValueError):
        speak_ack(data_dir=tmp_path, port=0)
    with pytest.raises(ValueError):
        speak_ack(data_dir=tmp_path)


def test_ack_sends_only_fixed_public_text_and_plays_verified_route(monkeypatch, tmp_path: Path):
    (tmp_path / "control-token").write_text("a" * 64, encoding="ascii")
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
    assert len(played) == 1 and played[0][0].startswith(b"RIFF")
