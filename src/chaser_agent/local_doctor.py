"""Read-only preflight for the private loopback HTTP runtime.

This never creates a directory, reads a bearer token, changes permissions, or
starts the service. A passing preflight is not a successful startup proof.
"""

from __future__ import annotations

import socket
from pathlib import Path

from chaser_agent.local_acl import InsecureRuntimePath, assert_private_runtime_path
from chaser_agent.local_http import LOOPBACK_HOST


def _path_state(path: Path, *, directory: bool) -> str:
    if path.is_symlink():
        return "symlink"
    if not path.exists():
        return "missing"
    if (directory and not path.is_dir()) or (not directory and not path.is_file()):
        return "wrong_type"
    try:
        assert_private_runtime_path(path)
    except InsecureRuntimePath as exc:
        message = str(exc).lower()
        if "broad" in message or "accessible to group or others" in message:
            return "insecure_acl"
        return "acl_unverified"
    except OSError:
        return "acl_unverified"
    return "private_acl"


def _port_state(port: int) -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((LOOPBACK_HOST, port))
    except OSError:
        return "unavailable_at_check"
    return "available_at_check"


def inspect_local_http_runtime(*, data_dir: Path, port: int) -> dict[str, object]:
    """Return bounded preflight state without reading or changing runtime data."""
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    states = {
        "runtime_directory": _path_state(data_dir, directory=True),
        "control_token_file": _path_state(data_dir / "control-token", directory=False),
        "runs_directory": _path_state(data_dir / "runs", directory=True),
    }
    port_status = _port_state(port)
    blocked = sorted(
        name for name, state in states.items()
        if state in {"symlink", "wrong_type", "insecure_acl", "acl_unverified"}
    )
    if port_status != "available_at_check":
        blocked.append("port")
    if blocked:
        result = "blocked"
    elif any(state == "missing" for state in states.values()):
        result = "incomplete"
    else:
        result = "preflight_clear"
    return {
        "result": result,
        "bind": LOOPBACK_HOST,
        "port": port,
        "port_status": port_status,
        "runtime_directory": str(data_dir),
        "path_states": states,
        "blocked_by": blocked,
        "token_value_read": False,
        "files_or_permissions_changed": False,
        "startup_verified": False,
    }


def format_local_http_report(report: dict[str, object]) -> str:
    """Render the same bounded preflight facts for a local operator."""
    state_labels = {
        "private_acl": "private ACL confirmed",
        "insecure_acl": "broad ACL blocks startup",
        "acl_unverified": "ACL could not be verified",
        "missing": "missing; creation has not been tested",
        "symlink": "symlink blocks startup",
        "wrong_type": "wrong file type blocks startup",
    }
    path_states = report["path_states"]
    lines = [
        f"Local HTTP preflight: {str(report['result']).replace('_', ' ')} (not a startup test)",
        f"Address: {report['bind']}:{report['port']}",
        "Port: available at this check" if report["port_status"] == "available_at_check"
        else "Port: unavailable at this check",
        f"Runtime directory: {state_labels[path_states['runtime_directory']]}",
        f"Control-token file: {state_labels[path_states['control_token_file']]} (value not read)",
        f"Runs directory: {state_labels[path_states['runs_directory']]}",
        "No file contents or token values were read; no files or permissions were changed.",
    ]
    return "\n".join(lines)
