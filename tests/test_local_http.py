"""Network-level checks for the bounded loopback source-review adapter."""

from __future__ import annotations

import http.client
import json
import socket
import threading
import time
from pathlib import Path

import pytest

from chaser_agent.local_http import (
    ARTIFACT_NAMES,
    LOOPBACK_HOST,
    LocalRequestHandler,
    MAX_CLIENT_WORKERS,
    SlidingWindowLimiter,
    create_server,
    load_or_create_token,
    validate_allowed_origin,
)
from chaser_agent.local_acl import InsecureRuntimePath

TOKEN = "a" * 64


@pytest.fixture(autouse=True)
def isolated_http_contract_fixtures(monkeypatch):
    # Pytest temp directories inherit workstation ACLs. ACL policy is tested
    # separately; endpoint tests use an injected private-storage premise.
    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", lambda _path: None)


def test_insecure_data_directory_refuses_token_creation(tmp_path: Path, monkeypatch):
    def reject(_path: Path):
        raise InsecureRuntimePath("broad ACL")

    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", reject)
    with pytest.raises(InsecureRuntimePath, match="broad ACL"):
        load_or_create_token(tmp_path)
    assert not (tmp_path / "control-token").exists()


def test_insecure_run_directory_refuses_server_start(tmp_path: Path, monkeypatch):
    def check(path: Path):
        if path.name == "runs":
            raise InsecureRuntimePath("broad ACL")

    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", check)
    with pytest.raises(InsecureRuntimePath, match="broad ACL"):
        create_server(data_dir=tmp_path, token=TOKEN, port=0)


@pytest.fixture
def api(tmp_path: Path):
    server = create_server(data_dir=tmp_path, token=TOKEN, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def call(api, method: str, path: str, *, payload=None, raw: bytes | None = None, headers=None):
    connection = http.client.HTTPConnection(LOOPBACK_HOST, api.server_port, timeout=5)
    body = raw if raw is not None else (json.dumps(payload).encode("utf-8") if payload is not None else None)
    request_headers = dict(headers or {})
    if body is not None:
        request_headers.setdefault("Content-Type", "application/json")
    connection.request(method, path, body=body, headers=request_headers)
    response = connection.getresponse()
    response_body = response.read()
    content_type = response.getheader("Content-Type", "")
    result = (
        json.loads(response_body) if response_body and content_type.startswith("application/json")
        else response_body if content_type.startswith("audio/")
        else response_body.decode("utf-8") if response_body else None
    )
    status = response.status
    returned_headers = dict(response.getheaders())
    connection.close()
    return status, result, returned_headers


def source_payload():
    return {
        "title": "Local research note",
        "text": "The system keeps source claims separate from agent inference. Operators must review actions before execution.",
        "privacy_class": "public_toy",
    }


def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def test_health_exposes_fixed_loopback_port_and_no_execution_claim(api):
    status, body, headers = call(api, "GET", "/v1/health")
    assert status == 200
    assert api.server_address[0] == LOOPBACK_HOST
    assert body["port"] == api.server_port
    assert body["mode"] == "deterministic_review_only"
    assert body["hud"] == "not_connected"
    assert body["voice"] == "not_connected"
    assert headers["Cache-Control"] == "no-store"


def test_hud_read_model_is_authenticated_and_inactive_without_executor(api):
    status, _, _ = call(api, "GET", "/v1/hud/current")
    assert status == 401
    status, hud, _ = call(api, "GET", "/v1/hud/current", headers=auth_headers())
    assert status == 200
    assert hud["status"] == "inactive"
    assert hud["controls_enabled"] is False
    assert hud["authority"] == "display_only_no_executor"


def test_hud_controls_are_auth_and_executor_gated(api):
    payload = {"session_id": "toy-session", "command": "pause"}
    status, _, _ = call(api, "POST", "/v1/hud/controls", payload=payload)
    assert status == 401
    status, body, _ = call(api, "POST", "/v1/hud/controls", payload=payload, headers=auth_headers())
    assert status == 409 and body["error"]["code"] == "hud_control_unavailable"
    status, _, _ = call(api, "POST", "/v1/hud/controls", payload={**payload, "extra": 1}, headers=auth_headers())
    assert status == 400

    class FakeExecutor:
        def __init__(self):
            self.calls = []

        def request_control(self, command, request_id):
            self.calls.append((command, request_id))

    executor = FakeExecutor()
    report = api.hud.attach("toy-session", executor)
    report(sequence=0, phase="running", action="Inspecting a toy page")
    status, state, _ = call(api, "GET", "/v1/hud/current", headers=auth_headers())
    assert status == 200 and state["controls_enabled"] is True
    status, submitted, _ = call(api, "POST", "/v1/hud/controls", payload=payload, headers=auth_headers())
    assert status == 202 and submitted["status"] == "pending_executor_ack"
    assert executor.calls == [("pause", submitted["request_id"])]
    assert submitted["hud"]["phase"] == "running"
    report(sequence=1, phase="paused", request_id=submitted["request_id"])
    status, state, _ = call(api, "GET", "/v1/hud/current", headers=auth_headers())
    assert status == 200 and state["phase"] == "paused"
    assert state["available_controls"] == ["resume", "stop", "take_over"]
    api.hud.detach()
    status, body, _ = call(api, "POST", "/v1/hud/controls", payload={"session_id": "toy-session", "command": "resume"}, headers=auth_headers())
    assert status == 409


def test_unauthorized_request_cannot_create_a_run(api):
    status, body, _ = call(api, "POST", "/v1/source-cards", payload=source_payload())
    assert status == 401
    assert body["error"]["code"] == "unauthorized"
    assert list(api.run_root.iterdir()) == []


def test_voice_is_disabled_by_default_and_never_accepts_private_text(api):
    payload = {"text": "Hello", "privacy_class": "public_toy"}
    status, body, _ = call(api, "POST", "/v1/voice/replies", payload=payload)
    assert status == 401
    status, body, _ = call(api, "POST", "/v1/voice/replies", payload=payload, headers=auth_headers())
    assert status == 503
    assert body["error"]["code"] == "voice_not_configured"
    for privacy_class in ("internal_safe", "private", []):
        payload["privacy_class"] = privacy_class
        status, _, _ = call(api, "POST", "/v1/voice/replies", payload=payload, headers=auth_headers())
        assert status == 400


def test_configured_voice_endpoint_returns_only_authenticated_audio(api, tmp_path):
    voice_id = "voice-20260927T120000000000Z-abcdef123456"
    wav = tmp_path / "response.wav"
    wav.write_bytes(b"RIFF" + b"x" * 64)

    class FakeVoice:
        def enqueue(self, text):
            assert text == "A public toy response."
            return {
                "voice_id": voice_id,
                "voice": "pocket-alba",
                "status": "queued",
                "status_url": f"/v1/voice/{voice_id}",
            }

        def status(self, candidate):
            return {
                "voice_id": voice_id,
                "status": "generated_pending_listening_review",
                "audio_url": f"/v1/voice/{voice_id}/audio.wav",
            } if candidate == voice_id else None

        def audio_path(self, candidate):
            return wav if candidate == voice_id else None

        def close(self):
            pass

        def runtime_state(self):
            return "ready"

    api.voice = FakeVoice()
    status, health, _ = call(api, "GET", "/v1/health")
    assert status == 200 and health["voice"] == "configured_local"
    assert health["voice_runtime"] == "ready"
    status, reply, _ = call(
        api, "POST", "/v1/voice/replies",
        payload={"text": "A public toy response.", "privacy_class": "public_toy"}, headers=auth_headers(),
    )
    assert status == 202
    assert reply["status"] == "queued"
    status, state, _ = call(api, "GET", reply["status_url"], headers=auth_headers())
    assert status == 200 and state["status"] == "generated_pending_listening_review"
    status, _, _ = call(api, "GET", state["audio_url"])
    assert status == 401
    status, audio, headers = call(api, "GET", state["audio_url"], headers=auth_headers())
    assert status == 200 and audio == wav.read_bytes()
    assert headers["Content-Type"] == "audio/wav"


def test_voice_cancel_is_authenticated_exact_and_does_not_expose_audio(api):
    voice_id = "voice-20260927T120000000000Z-abcdef123456"

    class FakeVoice:
        def cancel(self, candidate):
            return {"voice_id": candidate, "voice": "pocket-alba", "status": "cancelling"} if candidate == voice_id else None

        def status(self, _candidate):
            return {"voice_id": voice_id, "status": "cancelled"}

        def audio_path(self, _candidate):
            return None

        def close(self):
            pass

        def runtime_state(self):
            return "busy"

    api.voice = FakeVoice()
    path = f"/v1/voice/{voice_id}/cancel"
    status, _, _ = call(api, "POST", path, payload={})
    assert status == 401
    status, body, _ = call(api, "POST", path, payload={"extra": 1}, headers=auth_headers())
    assert status == 400 and body["error"]["code"] == "invalid_input"
    status, body, _ = call(api, "POST", path, payload={}, headers=auth_headers())
    assert status == 202 and body["status"] == "cancelling"
    status, _, _ = call(api, "GET", f"/v1/voice/{voice_id}/audio.wav", headers=auth_headers())
    assert status == 404
    status, _, _ = call(api, "POST", "/v1/voice/../cancel", payload={}, headers=auth_headers())
    assert status == 404


def test_source_card_round_trip_stays_review_only(api):
    payload = source_payload()
    payload["text"] += "\r\nA second line says café."
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=payload, headers=auth_headers())
    assert status == 201
    assert created["review_status"] == "pending_review"
    assert created["promotion_status"] == "not_promoted"
    run_id = created["run_id"]
    assert {path.name for path in (api.run_root / run_id).iterdir()} == ARTIFACT_NAMES | {".integrity.json"}

    status, index, _ = call(api, "GET", created["run_url"], headers=auth_headers())
    assert status == 200
    assert set(index["artifacts"]) == ARTIFACT_NAMES
    assert index["integrity_status"] == "verified"
    status, card, _ = call(api, "GET", f"/v1/runs/{run_id}/artifacts/source_card.json", headers=auth_headers())
    assert status == 200
    assert card["source_origin"] == "operator_submitted_local_http"
    assert card["source_claims"]
    assert card["promotion_status"] == "not_promoted"
    status, original, headers = call(api, "GET", f"/v1/runs/{run_id}/artifacts/original_source.md", headers=auth_headers())
    assert status == 200
    assert original == payload["text"]
    assert headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Run-Integrity"] == "verified"
    status, log, _ = call(api, "GET", f"/v1/runs/{run_id}/artifacts/run_log.json", headers=auth_headers())
    assert status == 200
    assert log["provider_calls"] == "none"
    assert log["browser_or_computer_use"] == "none"
    assert log["review_required"] is True
    assert log["integrity_version"] == 1


def test_changed_http_run_is_not_served_as_verified(api):
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    assert status == 201
    folder = api.run_root / created["run_id"]
    original = folder / "original_source.md"
    original.write_text(original.read_text(encoding="utf-8") + "\nAltered later.", encoding="utf-8")
    for path in (created["run_url"], f"{created['run_url']}/artifacts/source_card.json"):
        status, body, _ = call(api, "GET", path, headers=auth_headers())
        assert status == 409 and body["error"]["code"] == "run_integrity_failed"


def test_missing_new_integrity_record_fails_closed(api):
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    assert status == 201
    (api.run_root / created["run_id"] / ".integrity.json").unlink()
    status, body, _ = call(api, "GET", created["run_url"], headers=auth_headers())
    assert status == 409 and body["error"]["code"] == "run_integrity_failed"


def test_pre_manifest_run_is_explicitly_unverified(api):
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    assert status == 201
    folder = api.run_root / created["run_id"]
    (folder / ".integrity.json").unlink()
    log_path = folder / "run_log.json"
    run_log = json.loads(log_path.read_text(encoding="utf-8"))
    del run_log["integrity_version"]
    log_path.write_text(json.dumps(run_log), encoding="utf-8")
    status, body, headers = call(api, "GET", created["run_url"], headers=auth_headers())
    assert status == 200 and body["integrity_status"] == "unverified_legacy"
    assert headers["X-Run-Integrity"] == "unverified_legacy"


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"Host": "evil.example"}, 421),
        ({"Origin": "https://evil.example"}, 403),
        ({"Origin": "null"}, 403),
        ({"Origin": "http://127.0.0.1:4175"}, 403),
    ],
)
def test_host_and_origin_are_not_reflected_or_trusted(api, headers, expected):
    status, _, response_headers = call(api, "GET", "/v1/health", headers=headers)
    assert status == expected
    assert "Access-Control-Allow-Origin" not in response_headers


@pytest.mark.parametrize(
    ("path", "headers", "expected"),
    [
        ("/v1/voice/../cancel", {}, 404),
        ("/v1/source-cards", {"Host": "evil.example"}, 421),
        ("/v1/source-cards", {"Origin": "https://evil.example"}, 403),
    ],
)
def test_early_post_rejection_returns_response_with_small_body(api, path, headers, expected):
    status, _, _ = call(api, "POST", path, payload={"toy": "body"},
                        headers={**auth_headers(), **headers})
    assert status == expected


def test_exact_opt_in_origin_has_cors_but_still_requires_token(tmp_path):
    server = create_server(
        data_dir=tmp_path,
        token=TOKEN,
        port=0,
        allowed_origins=("http://127.0.0.1:4175",),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        headers = {"Origin": "http://127.0.0.1:4175"}
        status, _, response_headers = call(server, "OPTIONS", "/v1/source-cards", headers=headers)
        assert status == 204
        assert response_headers["Access-Control-Allow-Origin"] == headers["Origin"]
        status, _, _ = call(server, "POST", "/v1/source-cards", payload=source_payload(), headers=headers)
        assert status == 401
        status, _, response_headers = call(
            server, "OPTIONS", "/v1/voice/voice-20260927T120000000000Z-abcdef123456/cancel",
            headers=headers,
        )
        assert status == 204 and response_headers["Access-Control-Allow-Origin"] == headers["Origin"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize(
    ("raw", "headers", "expected"),
    [
        pytest.param(b'{"title":"x","title":"y","text":"z"}', {}, 400, id="duplicate-key"),
        pytest.param(b"{broken", {}, 400, id="malformed-json"),
        pytest.param(b"{}", {"Content-Type": "text/plain"}, 415, id="wrong-content-type"),
        pytest.param(b"x" * 262_145, {}, 413, id="oversized-body"),
    ],
)
def test_rejects_malformed_duplicate_non_json_and_oversized_bodies(api, raw, headers, expected):
    status, _, _ = call(api, "POST", "/v1/source-cards", raw=raw, headers={**auth_headers(), **headers})
    assert status == expected
    assert list(api.run_root.iterdir()) == []


def test_invalid_profile_and_unhashable_privacy_are_clean_errors(api):
    payload = source_payload()
    payload["profile"] = "no_such_profile"
    status, _, _ = call(api, "POST", "/v1/source-cards", payload=payload, headers=auth_headers())
    assert status == 400
    payload["profile"] = "general_source_review"
    payload["privacy_class"] = []
    status, _, _ = call(api, "POST", "/v1/source-cards", payload=payload, headers=auth_headers())
    assert status == 400
    assert list(api.run_root.iterdir()) == []


@pytest.mark.parametrize("privacy_class", ["scrubbed", "internal_safe", "private", "toy"])
def test_http_intake_rejects_non_public_privacy_classes(api, privacy_class):
    payload = source_payload()
    payload["privacy_class"] = privacy_class
    status, body, _ = call(api, "POST", "/v1/source-cards", payload=payload, headers=auth_headers())
    assert status == 400
    assert body["error"]["code"] == "invalid_input"
    assert list(api.run_root.iterdir()) == []


def test_run_paths_cannot_traverse_or_fetch_unlisted_files(api):
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    assert status == 201
    run_id = created["run_id"]
    for path in (
        f"/v1/runs/{run_id}/artifacts/../../control-token",
        f"/v1/runs/{run_id}/artifacts/%2e%2e",
        f"/v1/runs/{run_id}/artifacts/control-token",
        f"/v1/runs/{run_id}?file=control-token",
    ):
        status, _, _ = call(api, "GET", path, headers=auth_headers())
        assert status == 404


def test_authenticated_rate_limit_stops_repeated_creation(api):
    api.limiter = SlidingWindowLimiter(limit=1)
    first, _, _ = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    second, body, headers = call(api, "POST", "/v1/source-cards", payload=source_payload(), headers=auth_headers())
    assert first == 201
    assert second == 429
    assert body["error"]["code"] == "rate_limited"
    assert headers["Retry-After"] == "60"
    assert len(list(api.run_root.iterdir())) == 1


def test_client_worker_limit_rejects_excess_and_recovers(tmp_path):
    entered = threading.Event()
    release = threading.Event()

    class HoldingHandler(LocalRequestHandler):
        def handle(self):
            entered.set()
            release.wait(timeout=5)

    server = create_server(data_dir=tmp_path, token=TOKEN, port=0, max_client_workers=1)
    server.RequestHandlerClass = HoldingHandler
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    first = None
    second = None
    try:
        first = socket.create_connection((LOOPBACK_HOST, server.server_port), timeout=3)
        assert entered.wait(timeout=3)
        second = socket.create_connection((LOOPBACK_HOST, server.server_port), timeout=3)
        second.settimeout(3)
        response = second.recv(512)
        assert response.startswith(b"HTTP/1.1 503 Service Unavailable\r\n")
        assert b"Connection: close\r\n" in response
        server.RequestHandlerClass = LocalRequestHandler
        release.set()
        deadline = time.monotonic() + 3
        while True:
            status, body, _ = call(server, "GET", "/v1/health")
            if status == 200:
                assert body["port"] == server.server_port
                break
            assert status == 503 and time.monotonic() < deadline
            time.sleep(0.02)
    finally:
        release.set()
        if first is not None:
            first.close()
        if second is not None:
            second.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("limit", [0, MAX_CLIENT_WORKERS + 1])
def test_client_worker_limit_cannot_be_disabled_or_raised(tmp_path, limit):
    with pytest.raises(ValueError, match="Client worker limit"):
        create_server(data_dir=tmp_path, token=TOKEN, port=0, max_client_workers=limit)


def test_token_file_is_reused_without_exposing_it(tmp_path):
    first, path = load_or_create_token(tmp_path)
    second, same_path = load_or_create_token(tmp_path)
    assert first == second
    assert path == same_path
    assert len(first) == 64
    assert path.read_text(encoding="ascii").strip() == first


@pytest.mark.parametrize("origin", ["https://127.0.0.1:4175", "http://evil.example:4175", "http://127.0.0.1:4175/path"])
def test_allowed_origin_must_be_exact_loopback(origin):
    with pytest.raises(ValueError):
        validate_allowed_origin(origin)
