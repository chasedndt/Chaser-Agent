"""One-process local API/HUD ownership without a real desktop executor."""

from __future__ import annotations

import argparse
import http.client
import json
from pathlib import Path

import pytest

from chaser_agent.cli import run_desktop_command
from chaser_agent.local_acl import InsecureRuntimePath
from chaser_agent.local_desktop import run_desktop


@pytest.mark.parametrize("with_voice", [False, True])
def test_desktop_launcher_serves_loopback_then_stops_its_owned_server(tmp_path: Path, monkeypatch, with_voice):
    # Machine temp directories inherit workstation ACLs. The ACL policy has
    # separate tests; this test verifies one-process lifecycle and HTTP wiring.
    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", lambda _path: None)
    windows = []

    class FakeHudWindow:
        def __init__(self, *, port, token_file, show_idle, voice_model_dir, voice_output_enabled):
            self.port = port
            self.token_file = token_file
            assert show_idle is True
            assert voice_model_dir == (tmp_path / "model" if with_voice else None)
            assert voice_output_enabled is False
            self.closed = False
            windows.append(self)

        def run(self):
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
            try:
                connection.request("GET", "/v1/health")
                response = connection.getresponse()
                health = json.load(response)
                assert response.status == 200
                assert health["port"] == self.port
                assert health["hud"] == "not_connected"
                connection.request("GET", "/v1/hud/current")
                assert connection.getresponse().status == 401
            finally:
                connection.close()

        def close(self):
            self.closed = True

    monkeypatch.setattr("chaser_agent.local_desktop.HudWindow", FakeHudWindow)
    port = run_desktop(data_dir=tmp_path / "runtime", port=0,
                       voice_model_dir=tmp_path / "model" if with_voice else None)
    assert windows[0].closed
    assert windows[0].token_file.is_file()
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/v1/health")
        raise AssertionError("The launcher left its HTTP listener running")
    except OSError:
        pass
    finally:
        connection.close()


def test_desktop_cli_refuses_broad_runtime_before_hud(tmp_path: Path, monkeypatch, capsys):
    def reject(_data_dir):
        raise InsecureRuntimePath("broad ACL")

    monkeypatch.setattr("chaser_agent.local_desktop.load_or_create_token", reject)
    args = argparse.Namespace(data_dir=str(tmp_path), port=8765,
                              allowed_origin=[], voice_library=None, model_dir=None)
    assert run_desktop_command(args) == 2
    assert "broad ACL" in capsys.readouterr().err


def test_desktop_cli_rejects_invalid_port_without_runtime_changes(tmp_path: Path, capsys):
    args = argparse.Namespace(data_dir=str(tmp_path), port=0,
                              allowed_origin=[], voice_library=None, model_dir=None)
    assert run_desktop_command(args) == 2
    assert "port must be" in capsys.readouterr().err
    assert not (tmp_path / "control-token").exists()
