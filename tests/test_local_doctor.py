"""The local HTTP doctor reports preflight state without changing runtime data."""

import json
import socket
from pathlib import Path

import pytest

from chaser_agent.cli import main
from chaser_agent.local_acl import InsecureRuntimePath
from chaser_agent.local_doctor import inspect_local_http_runtime


def test_missing_runtime_is_incomplete_and_no_files_are_created(tmp_path, monkeypatch):
    target = tmp_path / "not-created"
    monkeypatch.setattr("chaser_agent.local_doctor._port_state", lambda _port: "available_at_check")
    report = inspect_local_http_runtime(data_dir=target, port=8765)
    assert report["result"] == "incomplete"
    assert report["path_states"] == {
        "runtime_directory": "missing",
        "control_token_file": "missing",
        "runs_directory": "missing",
    }
    assert report["token_value_read"] is False
    assert report["files_or_permissions_changed"] is False
    assert report["startup_verified"] is False
    assert not target.exists()


def test_broad_acl_is_blocked_without_reading_token(tmp_path, monkeypatch):
    (tmp_path / "runs").mkdir()
    (tmp_path / "control-token").write_text("private test value", encoding="ascii")

    def broad(_path):
        raise InsecureRuntimePath("Runtime path has broad Windows ACL access")

    def forbidden_read(_path, *args, **kwargs):
        raise AssertionError("doctor must not read token or artifact contents")

    monkeypatch.setattr("chaser_agent.local_doctor.assert_private_runtime_path", broad)
    monkeypatch.setattr("chaser_agent.local_doctor._port_state", lambda _port: "available_at_check")
    monkeypatch.setattr(Path, "read_text", forbidden_read)
    report = inspect_local_http_runtime(data_dir=tmp_path, port=8765)
    assert report["result"] == "blocked"
    assert report["path_states"] == {
        "runtime_directory": "insecure_acl",
        "control_token_file": "insecure_acl",
        "runs_directory": "insecure_acl",
    }
    assert report["blocked_by"] == ["control_token_file", "runs_directory", "runtime_directory"]


def test_occupied_loopback_port_is_reported_without_starting_service(tmp_path, monkeypatch):
    (tmp_path / "runs").mkdir()
    (tmp_path / "control-token").write_text("not-read", encoding="ascii")
    monkeypatch.setattr("chaser_agent.local_doctor.assert_private_runtime_path", lambda _path: None)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        report = inspect_local_http_runtime(data_dir=tmp_path, port=port)
        assert report["port_status"] == "unavailable_at_check"
        assert report["result"] == "blocked"
        assert report["blocked_by"] == ["port"]
    assert not (tmp_path / "new-file").exists()


def test_cli_prints_only_read_only_preflight_metadata(tmp_path, monkeypatch, capsys):
    (tmp_path / "runs").mkdir()
    (tmp_path / "control-token").write_text("never-print-this-value", encoding="ascii")
    monkeypatch.setattr("chaser_agent.local_doctor.assert_private_runtime_path", lambda _path: None)
    monkeypatch.setattr("chaser_agent.local_doctor._port_state", lambda _port: "available_at_check")
    assert main(["doctor", "--data-dir", str(tmp_path), "--port", "8765", "--json"]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["result"] == "preflight_clear"
    assert report["startup_verified"] is False
    assert "never-print-this-value" not in output


def test_cli_default_output_explains_preflight_without_token_value(tmp_path, monkeypatch, capsys):
    (tmp_path / "runs").mkdir()
    (tmp_path / "control-token").write_text("never-print-this-value", encoding="ascii")
    monkeypatch.setattr("chaser_agent.local_doctor.assert_private_runtime_path", lambda _path: None)
    monkeypatch.setattr("chaser_agent.local_doctor._port_state", lambda _port: "available_at_check")
    assert main(["doctor", "--data-dir", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "Address: 127.0.0.1:8765" in output
    assert "Control-token file: private ACL confirmed (value not read)" in output
    assert "not a startup test" in output
    assert "never-print-this-value" not in output


@pytest.mark.parametrize("port", [0, 65536])
def test_invalid_port_is_rejected_before_probe(tmp_path, port):
    with pytest.raises(ValueError, match="Port must be"):
        inspect_local_http_runtime(data_dir=tmp_path, port=port)
