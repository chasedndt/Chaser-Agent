"""Network-level checks for the bounded loopback source-review adapter."""

from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

import pytest

from chaser_agent.local_http import (
    ARTIFACT_NAMES,
    LOOPBACK_HOST,
    SlidingWindowLimiter,
    create_server,
    load_or_create_token,
    validate_allowed_origin,
)

TOKEN = "a" * 64


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
    result = (
        json.loads(response_body)
        if response_body and response.getheader("Content-Type", "").startswith("application/json")
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


def test_unauthorized_request_cannot_create_a_run(api):
    status, body, _ = call(api, "POST", "/v1/source-cards", payload=source_payload())
    assert status == 401
    assert body["error"]["code"] == "unauthorized"
    assert list(api.run_root.iterdir()) == []


def test_source_card_round_trip_stays_review_only(api):
    payload = source_payload()
    payload["text"] += "\r\nA second line says café."
    status, created, _ = call(api, "POST", "/v1/source-cards", payload=payload, headers=auth_headers())
    assert status == 201
    assert created["review_status"] == "pending_review"
    assert created["promotion_status"] == "not_promoted"
    run_id = created["run_id"]
    assert {path.name for path in (api.run_root / run_id).iterdir()} == ARTIFACT_NAMES

    status, index, _ = call(api, "GET", created["run_url"], headers=auth_headers())
    assert status == 200
    assert set(index["artifacts"]) == ARTIFACT_NAMES
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
    status, log, _ = call(api, "GET", f"/v1/runs/{run_id}/artifacts/run_log.json", headers=auth_headers())
    assert status == 200
    assert log["provider_calls"] == "none"
    assert log["browser_or_computer_use"] == "none"
    assert log["review_required"] is True


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
