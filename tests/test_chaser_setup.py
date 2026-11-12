"""Onboarding, settings, the Cloud key, the pre-flight checks and the shortcuts. No real key, no network beyond loopback."""

from __future__ import annotations

import http.server
import json
import os
import threading
from pathlib import Path

import pytest

from chaser_agent import chaser_cli, chaser_home, cloud_key, setup_checks, shortcuts
from chaser_agent.agent import AgentRuntime, Toolbox, WorkflowSpec
from chaser_agent.agent.reasoners import ChaseOSCloudReasoner, ScriptedReasoner
from chaser_agent.local_http import create_server, load_or_create_token

FAKE_KEY = "test-key-not-real-0123456789"
windows_only = pytest.mark.skipif(os.name != "nt", reason="the key is kept with Windows' per-user encryption")


# --- Settings -----------------------------------------------------------------

def test_settings_start_from_defaults_and_keep_what_is_saved() -> None:
    assert chaser_home.load()["port"] == 8765 and not chaser_home.is_onboarded()
    chaser_home.save({"reviewer": "Sam", "shortcuts": {"stop": "Ctrl+Alt+Shift+X"}})
    saved = chaser_home.load()
    assert saved["reviewer"] == "Sam" and saved["shortcuts"]["stop"] == "Ctrl+Alt+Shift+X"
    assert saved["shortcuts"]["take_over"] == "Ctrl+Alt+Shift+T"
    with pytest.raises(ValueError):
        chaser_home.save({"password": "x"})


# --- The Cloud key ------------------------------------------------------------

@windows_only
def test_a_saved_key_is_encrypted_readable_here_and_removable() -> None:
    target = cloud_key.save(FAKE_KEY)
    raw = target.read_text(encoding="ascii")
    assert FAKE_KEY not in raw and FAKE_KEY.encode("utf-16-le").hex() not in raw and bytes.fromhex(raw)
    assert cloud_key.load() == FAKE_KEY
    assert cloud_key.describe({}) == {"saved": True, "readable": True, "source": "saved", "file": str(target)}
    assert cloud_key.describe({"CHASEOS_CLOUD_KEY": "x"})["source"] == "environment"
    assert cloud_key.forget() and not cloud_key.forget() and cloud_key.load() == ""


def test_a_key_that_is_clearly_not_a_key_is_refused() -> None:
    for bad in ("", "short", "has space in it", "x" * 600):
        with pytest.raises(ValueError):
            cloud_key.validate(bad)
    assert cloud_key.validate(f"  {FAKE_KEY}\n") == FAKE_KEY


class _Usage(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.headers.get("Authorization") != f"Bearer {FAKE_KEY}":
            self.send_response(401)
            self.end_headers()
            return
        body = json.dumps({"credits": 65477, "plan": "pay-as-you-go"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        pass


@pytest.fixture
def usage_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _Usage)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_checking_a_key_reads_the_balance_and_names_a_refusal(usage_server) -> None:
    assert cloud_key.check(FAKE_KEY, base_url=usage_server) == {"ok": True, "credits": 65477, "plan": "pay-as-you-go"}
    refused = cloud_key.check("wrong-key-123456", base_url=usage_server)
    assert refused["ok"] is False and refused["refused"] is True
    unreachable = cloud_key.check(FAKE_KEY, base_url="http://127.0.0.1:9", timeout=2)
    assert unreachable["ok"] is False and not unreachable.get("refused")


@windows_only
def test_the_cloud_route_uses_the_environment_first_then_the_saved_key() -> None:
    assert ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "env-key-123"}).key_source == "environment"
    assert ChaseOSCloudReasoner.from_environment({}).key_source == "none"  # a given environment never reads the disk unless asked
    cloud_key.save(FAKE_KEY)
    route = ChaseOSCloudReasoner.from_environment({}, saved=True)
    assert route.key_source == "saved" and route.status()["available"]
    route.set_key("")
    assert route.key_source == "none" and not route.status()["available"] and "chaser key add" in route.status()["reason"]


# --- Shortcuts ----------------------------------------------------------------

def test_shortcuts_refuse_chords_windows_or_the_keyboard_already_uses() -> None:
    assert shortcuts.label("ctrl+alt+pause") == "Ctrl+Alt+Pause"
    assert shortcuts.label("Shift+Ctrl+Alt+t") == "Ctrl+Alt+Shift+T"
    for chord, words in (("Ctrl+Alt+Delete", "Windows uses"), ("Ctrl+Alt+End", "Remote Desktop"), ("Win+S", "Windows key"),
                         ("Ctrl+S", "Ctrl and Alt"), ("Ctrl+Alt+E", "AltGr"), ("Ctrl+Alt+F12", "letter")):
        with pytest.raises(ValueError, match=words):
            shortcuts.parse(chord)


def test_two_shortcuts_cannot_share_keys() -> None:
    chosen = dict(chaser_home.DEFAULT_SHORTCUTS)
    with pytest.raises(ValueError, match="already uses"):
        shortcuts.check_choice("take_over", "Ctrl+Alt+Pause", chosen)
    rows = shortcuts.overview(chosen)
    assert [row["name"] for row in rows] == ["stop", "stop_fallback", "take_over"] and rows[0]["keys"] == ["Ctrl", "Alt", "Pause"]


# --- Pre-flight checks --------------------------------------------------------

def test_checks_say_what_is_missing_and_never_show_a_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(setup_checks.shutil, "which", lambda _name: None)
    settings = {**chaser_home.load(), "data_dir": str(tmp_path / "missing"), "port": 1, "packs": [str(tmp_path / "nope.py")]}
    report = setup_checks.run(settings, environ={"CHASEOS_CLOUD_KEY": FAKE_KEY})
    rows = {row["id"]: row for row in report["rows"]}
    assert rows["data_folder"]["state"] == "warn" and "doesn't exist" in rows["data_folder"]["detail"]
    assert rows["cloud_key"]["state"] == "ok" and rows["routes"]["state"] == "ok"
    assert rows["packs"]["state"] == "fail" and rows["reviewer"]["state"] == "warn"
    assert report["result"] == "fail" and FAKE_KEY not in json.dumps(report)
    without = {row["id"]: row for row in setup_checks.run(settings, environ={})["rows"]}
    assert without["routes"]["state"] == "fail" and without["cloud_key"]["fix"]


# --- The HUD's settings routes ------------------------------------------------

@pytest.fixture
def served(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", lambda _path: None)
    token, _ = load_or_create_token(tmp_path)
    cloud = ChaseOSCloudReasoner("")
    runtime = AgentRuntime(tmp_path, toolbox=Toolbox(), reasoners=[cloud, ScriptedReasoner([])])
    runtime.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset()))
    server = create_server(data_dir=tmp_path, token=token, port=0, agent=runtime)
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield server, token, cloud
    server.shutdown()
    server.server_close()


def _call(server, token, method, path, body=None):
    import http.client

    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
    headers = {"Host": f"127.0.0.1:{server.server_port}", "Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    connection.request(method, path, body=data, headers=headers)
    response = connection.getresponse()
    payload = response.read()
    connection.close()
    return response.status, payload


def test_settings_need_the_token(served) -> None:
    server, _, _ = served
    assert _call(server, "0" * 64, "GET", "/v1/agent/setup")[0] == 401


@windows_only
def test_a_key_added_in_the_hud_is_used_at_once_and_never_sent_back(served) -> None:
    server, token, cloud = served
    status, body = _call(server, token, "GET", "/v1/agent/setup")
    assert status == 200 and json.loads(body)["key"] == {"in_use": False, "source": "none", "saved": False}
    status, body = _call(server, token, "POST", "/v1/agent/setup/key", {"key": FAKE_KEY, "check": False})
    assert status == 200 and FAKE_KEY.encode() not in body
    assert json.loads(body)["key"] == {"in_use": True, "source": "saved", "saved": True}
    assert cloud.status()["available"] and cloud_key.load() == FAKE_KEY
    status, body = _call(server, token, "POST", "/v1/agent/setup/key/remove", {})
    assert status == 200 and json.loads(body)["removed"] and not cloud.status()["available"]


def test_a_refused_key_is_not_saved(served, monkeypatch: pytest.MonkeyPatch) -> None:
    server, token, cloud = served
    monkeypatch.setattr(cloud_key, "check", lambda _key: {"ok": False, "refused": True, "reason": "ChaseOS Cloud didn't accept this key."})
    status, body = _call(server, token, "POST", "/v1/agent/setup/key", {"key": FAKE_KEY})
    assert status == 400 and b"didn't accept" in body and not cloud_key.path().exists() and not cloud.status()["available"]


def test_name_shortcuts_and_onboarding_are_saved_from_the_hud(served) -> None:
    server, token, _ = served
    status, body = _call(server, token, "POST", "/v1/agent/setup/profile", {"reviewer": "  Sam   Lee ", "onboarded": True})
    value = json.loads(body)
    assert status == 200 and value["reviewer"] == "Sam Lee" and value["onboarded"]
    status, body = _call(server, token, "POST", "/v1/agent/setup/shortcuts", {"name": "stop", "chord": "Ctrl+Alt+E"})
    assert status == 400 and b"AltGr" in body
    status, body = _call(server, token, "POST", "/v1/agent/setup/shortcuts", {"reset": True})
    assert status == 200 and json.loads(body)["shortcuts"][0]["chord"] == "Ctrl+Alt+Pause"
    status, body = _call(server, token, "GET", "/v1/agent/setup/checks")
    rows = {row["id"]: row for row in json.loads(body)["rows"]}
    assert status == 200 and rows["gateway"]["state"] == "ok" and rows["reviewer"]["detail"] == 'Approvals are signed "Sam Lee"'


def test_the_hud_has_settings_and_a_first_run_card(served) -> None:
    server, token, _ = served
    _, page = _call(server, token, "GET", "/")
    for marker in (b'id="settings-button"', b'id="settings"', b'id="welcome"'):
        assert marker in page
    _, script = _call(server, token, "GET", "/console/app.js")
    assert b"/v1/agent/setup/key" in script and b"decided_by: decidedBy" in script


# --- The chaser command -------------------------------------------------------

def test_the_gateway_starts_the_service_with_the_saved_settings(tmp_path: Path) -> None:
    chaser_home.save({"data_dir": str(tmp_path / "data"), "port": 8799, "packs": [str(tmp_path / "pack.py")], "memory_limit_mb": 900})
    command = chaser_cli.gateway_command(chaser_home.load())
    assert command[3:6] == ["-m", "chaser_agent.cli", "serve"]
    assert command[command.index("--port") + 1] == "8799" and command[command.index("--pack") + 1].endswith("pack.py")
    assert FAKE_KEY not in " ".join(command)


def test_onboarding_without_a_terminal_uses_flags_and_asks_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    made = []
    monkeypatch.setattr(setup_checks, "make_private_folder", lambda folder: made.append(folder) or folder.mkdir(parents=True))
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("asked a question"))
    code = chaser_cli.main(["onboard", "--non-interactive", "--no-start", "--data-dir", str(tmp_path / "data"), "--port", "8798", "--reviewer", "Sam"])
    out = capsys.readouterr().out
    saved = chaser_home.load()
    assert code == 0 and saved["reviewer"] == "Sam" and saved["port"] == 8798 and saved["onboarded_at"] and made
    assert "Step 6 of 6" in out and "Not started" in out


def test_chaser_alone_points_to_onboarding_until_set_up(capsys, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chaser_cli, "interactive_terminal", lambda: False)
    assert chaser_cli.main([]) == 0 and "chaser onboard" in capsys.readouterr().out
