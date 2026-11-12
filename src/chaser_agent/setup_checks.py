"""Pre-flight checks: can Chaser run on this computer, and what's missing. Read-only unless asked to fix.

`chaser doctor`, `chaser onboard` and the HUD's Checks panel all show these rows. Each row says what
was found and, when something is missing, the one thing to do about it. The key is never shown.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

from chaser_agent import chaser_home, cloud_key, shortcuts

OK, WARN, FAIL, INFO = "ok", "warn", "fail", "info"
EDGE = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
PRIVATE_FOLDER_PS = r"""
$path=$env:CHASER_PRIVATE_FOLDER
New-Item -ItemType Directory -Force -Path $path|Out-Null
$acl=Get-Acl -LiteralPath $path
$acl.SetAccessRuleProtection($true,$false)
foreach($rule in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($rule)}
foreach($sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))){
  $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
}
Set-Acl -LiteralPath $path -AclObject $acl
"""


def row(check_id: str, title: str, state: str, detail: str, fix: str | None = None) -> dict[str, Any]:
    return {"id": check_id, "title": title, "state": state, "detail": detail, "fix": fix}


def gateway_health(port: int, timeout: float = 1.5) -> dict[str, Any] | None:
    """The running service's health answer, or None if nothing answers. Health needs no token."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health", timeout=timeout) as response:  # noqa: S310 - loopback
            value = json.loads(response.read().decode("utf-8"))
            return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def port_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def make_private_folder(folder: Path) -> None:
    """Create the data folder so only this account, SYSTEM and Administrators can open it, as the service requires."""
    if os.name != "nt":
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(folder, 0o700)
        return
    done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PRIVATE_FOLDER_PS],
                          env={**os.environ, "CHASER_PRIVATE_FOLDER": str(folder)}, capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise OSError(f"Couldn't make {folder} private: {done.stderr.strip()[:300]}")


def _folder(settings: dict[str, Any]) -> dict[str, Any]:
    from chaser_agent.local_doctor import _path_state

    folder = Path(settings["data_dir"])
    state = _path_state(folder, directory=True)
    if state == "private_acl":
        return row("data_folder", "Where Chaser keeps its work", OK, f"{folder}, private to you")
    if state == "missing":
        return row("data_folder", "Where Chaser keeps its work", WARN, f"{folder} doesn't exist yet", "chaser doctor --fix creates it, private to you")
    return row("data_folder", "Where Chaser keeps its work", FAIL, f"{folder} isn't private ({state.replace('_', ' ')})",
               "Pick another folder with chaser setup, or remove other people's access to it")


def _gateway(port: int) -> dict[str, Any]:
    health = gateway_health(port)
    if health and health.get("service") == "chaser-agent":
        mode = "Running, ready for work" if health.get("agent") == "ready" else "Running in review-only mode"
        return row("gateway", "Chaser's service", OK, f"{mode} on 127.0.0.1:{port}")
    if port_free(port):
        return row("gateway", "Chaser's service", INFO, "Not running", "chaser gateway starts it")
    return row("gateway", "Chaser's service", FAIL, f"Another program is using port {port}", "Choose another port with chaser setup")


def _key(online: bool, environ: dict[str, str]) -> tuple[dict[str, Any], bool]:
    found = cloud_key.describe(environ)
    title = "ChaseOS Cloud key"
    if found["source"] == "none":
        if found["saved"]:
            return row("cloud_key", title, FAIL, "Saved, but this Windows account can't decrypt it", "Add the key again: chaser key add"), False
        return row("cloud_key", title, WARN, "Not added. Chaser can still use Claude Code if it's installed", "Add one in Settings, or run: chaser key add"), False
    where = "Set for this session by your vault" if found["source"] == "environment" else "Saved for this Windows account only"
    if not online:
        return row("cloud_key", title, OK, where), True
    result = cloud_key.check(environ.get("CHASEOS_CLOUD_KEY") or cloud_key.load())
    if result["ok"]:
        credits = f", {result['credits']:,.0f} credits left" if result.get("credits") is not None else ""
        return row("cloud_key", title, OK, f"{where}. ChaseOS Cloud accepts it{credits}"), True
    refused = bool(result.get("refused"))
    return row("cloud_key", title, FAIL if refused else WARN, f"{where}. {result['reason']}", "chaser key add to replace it" if refused else None), not refused


def run(settings: dict[str, Any] | None = None, *, online: bool = False, environ: dict[str, str] | None = None,
        running: dict[str, Any] | None = None) -> dict[str, Any]:
    """running: when the service itself asks, what it already knows (its port and Cloud key source)."""
    settings = settings or chaser_home.load()
    environ = os.environ if environ is None else environ
    rows = []
    version = ".".join(map(str, sys.version_info[:3]))
    rows.append(row("python", "Python", OK if sys.version_info >= (3, 11) else FAIL, f"Python {version}",
                    None if sys.version_info >= (3, 11) else "Chaser needs Python 3.11 or newer"))
    rows.append(_folder(settings))
    if running:
        rows.append(row("gateway", "Chaser's service", OK, f"Running, ready for work on 127.0.0.1:{running['port']}"))
        if running.get("key_source") == "environment":
            environ = {**environ, "CHASEOS_CLOUD_KEY": running.get("key") or ""}
    else:
        rows.append(_gateway(int(settings["port"])))
    key_row, has_cloud = _key(online, environ)
    rows.append(key_row)
    claude = shutil.which("claude")
    rows.append(row("claude_code", "Claude Code", OK if claude else INFO,
                    "Found. Chaser can use your Claude Code sign-in" if claude else "Not installed (optional)"))
    rows.append(row("routes", "A way for Chaser to think", OK if (has_cloud or claude) else FAIL,
                    "ChaseOS Cloud" if has_cloud and not claude else "Claude Code" if claude and not has_cloud else "ChaseOS Cloud, then Claude Code" if claude else "None yet",
                    None if (has_cloud or claude) else "Add a ChaseOS Cloud key, or install and sign in to Claude Code"))
    missing = [pack for pack in settings.get("packs") or [] if not Path(pack).is_file()]
    if settings.get("packs"):
        rows.append(row("packs", "Packs", FAIL if missing else OK,
                        f"{len(missing)} not found: {', '.join(missing)}" if missing else f"{len(settings['packs'])} loaded at start",
                        "Fix the path with chaser setup" if missing else None))
    if os.name == "nt":
        rows.append(row("hud", "The HUD window", OK if EDGE.is_file() else WARN,
                        "Microsoft Edge is installed" if EDGE.is_file() else "Microsoft Edge wasn't found", None if EDGE.is_file() else "Install Edge, or open the HUD in any browser"))
    keys = shortcuts.overview(settings.get("shortcuts") or {})
    clashes = [item["title"] for item in keys if item["state"] in {"taken", "invalid"}]
    rows.append(row("shortcuts", "Keys that stop Chaser", WARN if clashes else OK,
                    f"Can't use: {', '.join(clashes)}" if clashes else "All free on this computer", "chaser shortcuts to change them" if clashes else None))
    reviewer = (settings.get("reviewer") or "").strip()
    rows.append(row("reviewer", "Your name on approvals", OK if reviewer else WARN,
                    f"Approvals are signed \"{reviewer}\"" if reviewer else "Approvals are signed \"local_operator\"", None if reviewer else "Set it in Settings, or run: chaser setup"))
    states = {item["state"] for item in rows}
    result = FAIL if FAIL in states else WARN if WARN in states else OK
    return {"result": result, "rows": rows, "online": online, "key_shown": False}


def fix(settings: dict[str, Any] | None = None) -> list[str]:
    """The safe fixes: create the private data folder. Returns what was done."""
    settings = settings or chaser_home.load()
    done = []
    folder = Path(settings["data_dir"])
    if not folder.exists():
        make_private_folder(folder)
        done.append(f"Created {folder}, private to you")
    return done
