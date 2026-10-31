"""The agent's routes on the real loopback server, with a scripted reasoner."""

from __future__ import annotations

import http.client
import json
import threading
import time
from pathlib import Path

import pytest

from chaser_agent.agent import AgentRuntime, Toolbox, WorkflowSpec
from chaser_agent.agent.reasoners import BridgeReasoner, ScriptedReasoner
from chaser_agent.local_http import create_server, load_or_create_token


def _reply(thought: str, action: dict) -> str:
    return json.dumps({"thought": thought, "actions": [action]})


@pytest.fixture
def served(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", lambda _path: None)
    token, _ = load_or_create_token(tmp_path)
    bridge = BridgeReasoner()
    runtime = AgentRuntime(tmp_path, toolbox=Toolbox(), reasoners=[ScriptedReasoner([_reply("hello", {"type": "final", "answer": "Hi."})]), bridge])
    runtime.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset()))
    server = create_server(data_dir=tmp_path, token=token, port=0, agent=runtime)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    yield server, token, runtime
    server.shutdown()
    server.server_close()


def _request(server, method: str, path: str, token: str | None = None, body: dict | None = None) -> tuple[int, bytes, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    headers = {"Host": f"127.0.0.1:{server.server_port}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    connection.request(method, path, body=data, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    result = response.status, payload, dict(response.getheaders())
    connection.close()
    return result


def test_health_says_the_agent_is_ready(served) -> None:
    server, _, _ = served
    status, body, _ = _request(server, "GET", "/v1/health")
    assert status == 200
    assert json.loads(body)["agent"] == "ready"


def test_agent_routes_require_the_token(served) -> None:
    server, _, _ = served
    for path in ("/v1/agent/status", "/v1/agent/sessions", "/v1/agent/reasoner/next"):
        assert _request(server, "GET", path)[0] == 401
    assert _request(server, "POST", "/v1/agent/sessions", body={"message": "hi"})[0] == 401


def test_session_runs_over_http_and_its_events_are_readable(served) -> None:
    server, token, runtime = served
    status, body, _ = _request(server, "POST", "/v1/agent/sessions", token, {"message": "Say hello", "reasoner": "scripted"})
    assert status == 201
    session = json.loads(body)
    runtime.wait(session["id"])
    _, body, _ = _request(server, "GET", f"/v1/agent/sessions/{session['id']}", token)
    snapshot = json.loads(body)
    assert snapshot["status"] == "finished"
    assert snapshot["final_answer"] == "Hi."
    _, body, _ = _request(server, "GET", f"/v1/agent/sessions/{session['id']}/events?after=0", token)
    kinds = [event["type"] for event in json.loads(body)["events"]]
    assert kinds[0] == "session_created"
    assert kinds[-1] == "turn_finished"


def test_session_fields_outside_the_contract_are_refused(served) -> None:
    server, token, _ = served
    status, _, _ = _request(server, "POST", "/v1/agent/sessions", token, {"message": "hi", "grants": ["mail_send_approved"]})
    assert status == 400


def test_bridge_round_trip_over_http(served) -> None:
    server, token, runtime = served
    _, body, _ = _request(server, "POST", "/v1/agent/sessions", token, {"message": "Say hello", "reasoner": "bridge"})
    session = json.loads(body)
    request = None
    for _ in range(100):
        _, body, _ = _request(server, "GET", "/v1/agent/reasoner/next", token)
        request = json.loads(body)["request"]
        if request:
            break
        time.sleep(0.02)
    assert request
    status, _, _ = _request(server, "POST", "/v1/agent/reasoner/reply", token, {"request_id": request["request_id"], "text": _reply("hi", {"type": "final", "answer": "From the bridge."})})
    assert status == 202
    runtime.wait(session["id"])
    assert runtime.snapshot(session["id"])["final_answer"] == "From the bridge."


def test_console_loads_without_the_token_but_holds_no_data(served) -> None:
    server, _, _ = served
    status, body, headers = _request(server, "GET", "/")
    assert status == 200
    assert b"Chaser Agent" in body
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert _request(server, "GET", "/console/app.js")[0] == 200
    assert _request(server, "GET", "/assets/motion/compiling.png")[0] == 200
    assert _request(server, "GET", "/assets/motion/../../../secret.png")[0] in {401, 404}


def test_the_page_is_the_small_hud_with_no_side_panels(served) -> None:
    server, _, _ = served
    _, body, _ = _request(server, "GET", "/")
    page = body.decode("utf-8")
    assert 'id="hud"' in page and 'id="stop"' in page and "Tell Chaser Agent what to do" in page
    for removed in ('class="side"', 'id="tray"', 'id="routes"', 'id="grants"'):
        assert removed not in page
    _, script, _ = _request(server, "GET", "/console/app.js")
    assert b"Tell Chaser " not in script.replace(b"Tell Chaser Agent", b"")


def test_a_bridge_nobody_is_answering_does_not_count_as_connected() -> None:
    from chaser_agent.agent.reasoners import BridgeReasoner

    bridge = BridgeReasoner()
    assert bridge.status()["connected"] is False
    assert bridge.status()["reason"]
    bridge.next_request()
    assert bridge.status()["connected"] is True
    assert bridge.status()["reason"] is None


def test_auto_uses_the_bridge_only_while_something_is_answering_it(tmp_path) -> None:
    from chaser_agent.agent import AgentRuntime, Toolbox, WorkflowSpec
    from chaser_agent.agent.reasoners import BridgeReasoner, ReasonerUnavailable

    bridge = BridgeReasoner()
    runtime = AgentRuntime(tmp_path, toolbox=Toolbox(), reasoners=[bridge])
    runtime.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset()))
    with pytest.raises(ReasonerUnavailable, match="No AI model is connected"):
        runtime._resolve_reasoner({"reasoner_id": "auto"})
    bridge.next_request()
    assert runtime._resolve_reasoner({"reasoner_id": "auto"}) is bridge


def test_the_status_names_a_parent_only_when_a_pack_sets_one(served) -> None:
    server, token, runtime = served
    status = json.loads(_request(server, "GET", "/v1/agent/status", token)[1])
    assert status["parent"] is None
    runtime.parent_link = {"label": "Parent", "url": "http://127.0.0.1:1/"}
    assert json.loads(_request(server, "GET", "/v1/agent/status", token)[1])["parent"]["label"] == "Parent"


def test_artifact_paths_cannot_escape_the_workspace(served) -> None:
    server, token, runtime = served
    _, body, _ = _request(server, "POST", "/v1/agent/sessions", token, {"message": "Say hello", "reasoner": "scripted"})
    session = json.loads(body)
    runtime.wait(session["id"])
    status, _, _ = _request(server, "GET", f"/v1/agent/sessions/{session['id']}/artifacts/..%2F..%2Fsession.json", token)
    assert status == 404
    status, _, _ = _request(server, "GET", f"/v1/agent/sessions/{session['id']}/artifacts/../session.json", token)
    assert status == 404
