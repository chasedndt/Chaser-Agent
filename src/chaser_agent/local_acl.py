"""Read-only privacy gate for local HTTP runtime files.

Never rewrites ACLs. On Windows, startup refuses a runtime directory that
grants access beyond the current user, SYSTEM, and Administrators.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path


class InsecureRuntimePath(ValueError):
    pass


def _allowed_windows_sddl(sddl: str, current_sid: str) -> bool:
    if not re.fullmatch(r"S-1-[0-9-]+", current_sid):
        return False
    if not sddl.startswith("O:"):
        return False
    owner_end = min((index for marker in ("G:", "D:")
                     if (index := sddl.find(marker, 2)) >= 0), default=-1)
    if owner_end < 0 or sddl[2:owner_end] not in {current_sid, "BA", "SY", "S-1-5-18", "S-1-5-32-544"}:
        return False
    dacl_start = sddl.find("D:")
    if dacl_start < 0:
        return False
    dacl_end = sddl.find("S:", dacl_start + 2)
    dacl = sddl[dacl_start + 2:dacl_end if dacl_end >= 0 else len(sddl)]
    flags = re.match(r"(?:P|AI|AR)*", dacl)
    ace_text = dacl[flags.end():] if flags else dacl
    if not re.fullmatch(r"(?:\([^()]*\))+", ace_text):
        return False
    aces = re.findall(r"\(([^()]*)\)", ace_text)
    permitted = {current_sid, "BA", "SY", "S-1-5-18", "S-1-5-32-544"}
    has_user_grant = False
    for ace in aces:
        parts = ace.split(";")
        if len(parts) != 6:
            return False
        kind, _, _, _, _, trustee = parts
        if kind in {"A", "OA"}:
            if trustee not in permitted:
                return False
            if trustee == current_sid:
                has_user_grant = True
        elif kind not in {"D", "OD"}:
            return False
    return has_user_grant


def _windows_acl(path: Path) -> tuple[str, str]:
    shell = shutil.which("pwsh") or shutil.which("powershell.exe")
    if shell is None:
        raise InsecureRuntimePath("Windows ACL inspection is unavailable")
    script = (
        "$ErrorActionPreference='Stop'; "
        "$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; "
        "$acl=Get-Acl -LiteralPath $env:CHASER_ACL_TARGET; "
        "Write-Output $sid; Write-Output $acl.Sddl"
    )
    environment = {**os.environ, "CHASER_ACL_TARGET": str(path)}
    try:
        result = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-Command", script],
            env=environment, capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InsecureRuntimePath("Windows ACL inspection failed") from exc
    lines = result.stdout.strip().splitlines()
    if result.returncode or len(lines) != 2:
        raise InsecureRuntimePath(f"Windows ACL inspection failed (exit {result.returncode}, lines {len(lines)})")
    return lines[0].strip(), lines[1].strip()


def assert_private_runtime_path(path: Path) -> None:
    """Fail closed before reading tokens or writing artifacts."""
    if path.is_symlink() or not path.exists():
        raise InsecureRuntimePath("Runtime path is missing or is a symlink")
    if os.name == "nt":
        sid, sddl = _windows_acl(path)
        if not _allowed_windows_sddl(sddl, sid):
            raise InsecureRuntimePath("Runtime path has broad Windows ACL access; no permissions were changed")
    else:
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            raise InsecureRuntimePath("Runtime path is accessible to group or others")
