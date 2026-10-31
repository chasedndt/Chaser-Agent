"""Read-only privacy gate for local HTTP runtime files.

Never rewrites ACLs. On Windows, startup refuses a runtime directory that
grants access beyond the current user, SYSTEM, and Administrators.
"""

from __future__ import annotations

import ctypes
import os
import re
import stat
from pathlib import Path

_TOKEN_QUERY = 0x0008
_TOKEN_USER = 1
_SE_FILE_OBJECT = 1
_SDDL_REVISION_1 = 1
_ACL_FIELDS = 0x1 | 0x2 | 0x4  # Owner, group and DACL.


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
    owned_by_user = sddl[2:owner_end] == current_sid
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
            # Python 3.12+ os.mkdir(mode=0o700) writes "owner rights", which is only as
            # private as the owner: it counts as the user only when the user owns the path.
            if trustee == "OW" and owned_by_user:
                trustee = current_sid
            if trustee not in permitted:
                return False
            if trustee == current_sid:
                has_user_grant = True
        elif kind not in {"D", "OD"}:
            return False
    return has_user_grant


def _windows_acl(path: Path) -> tuple[str, str]:
    """The current user's SID and the path's owner, group and DACL, from the Windows API.

    Starting PowerShell for each path took seconds and could time out on a busy machine.
    """
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
    advapi32.GetNamedSecurityInfoW.argtypes = [
        wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p), ctypes.c_void_p,
    ]

    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), _TOKEN_QUERY, ctypes.byref(token)):
        raise InsecureRuntimePath("Windows ACL inspection failed: no process token")
    try:
        needed = wintypes.DWORD()
        advapi32.GetTokenInformation(token, _TOKEN_USER, None, 0, ctypes.byref(needed))
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(token, _TOKEN_USER, buffer, needed, ctypes.byref(needed)):
            raise InsecureRuntimePath("Windows ACL inspection failed: no token user")
    finally:
        kernel32.CloseHandle(token)
    user_sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
    sid_text = ctypes.c_wchar_p()
    if not advapi32.ConvertSidToStringSidW(user_sid, ctypes.byref(sid_text)):
        raise InsecureRuntimePath("Windows ACL inspection failed: unreadable user")
    try:
        sid = sid_text.value or ""
    finally:
        kernel32.LocalFree(sid_text)

    descriptor = ctypes.c_void_p()
    status = advapi32.GetNamedSecurityInfoW(str(path), _SE_FILE_OBJECT, _ACL_FIELDS, None, None, None, None, ctypes.byref(descriptor))
    if status:
        raise InsecureRuntimePath(f"Windows ACL inspection failed (error {status})")
    sddl_text = ctypes.c_wchar_p()
    try:
        if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, _SDDL_REVISION_1, _ACL_FIELDS, ctypes.byref(sddl_text), None):
            raise InsecureRuntimePath("Windows ACL inspection failed: unreadable descriptor")
        sddl = sddl_text.value or ""
        kernel32.LocalFree(sddl_text)
    finally:
        kernel32.LocalFree(descriptor)
    return sid, sddl


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


def read_private_control_token(data_dir: Path) -> str:
    """Read a local control credential only after checking both storage ACLs."""
    assert_private_runtime_path(data_dir)
    token_path = data_dir / "control-token"
    assert_private_runtime_path(token_path)
    token = token_path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise InsecureRuntimePath("Local control token is invalid")
    return token
