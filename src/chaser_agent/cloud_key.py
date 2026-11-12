"""This computer's ChaseOS Cloud key: saved encrypted for the current Windows user, and checked for free.

The file is the same one scripts/Save-ChaseOSCloudKey.ps1 writes (a DPAPI blob of the key in UTF-16,
as hex), so the PowerShell scripts, `chaser key` and the HUD all read and write one key. Another
account or computer can't decrypt it. Nothing here prints, logs or returns the key itself.

A key in CHASEOS_CLOUD_KEY still wins, so a vault that injects it (ChaseOS Studio's Secrets) keeps working.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from chaser_agent import chaser_home

KEY_FILE = "chaseos-cloud-key.dpapi"
MIN_LENGTH = 8
MAX_LENGTH = 512


class KeyStoreUnavailable(RuntimeError):
    """Saving a key needs Windows' per-user encryption."""


def path() -> Path:
    return chaser_home.home() / KEY_FILE


def validate(key: str) -> str:
    key = (key or "").strip()
    if len(key) < MIN_LENGTH:
        raise ValueError("That is too short to be a ChaseOS Cloud key.")
    if len(key) > MAX_LENGTH or any(ch.isspace() for ch in key) or not key.isprintable():
        raise ValueError("That doesn't look like a ChaseOS Cloud key. Paste the key on its own.")
    return key


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise KeyStoreUnavailable("Saving a key needs Windows. Set CHASEOS_CLOUD_KEY for the service instead.")
    import ctypes
    import ctypes.wintypes as wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buffer = ctypes.create_string_buffer(data, len(data))
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    result = Blob()
    call = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if not call(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)):
        raise KeyStoreUnavailable("Windows could not " + ("encrypt" if protect else "decrypt") + " the key for this account.")
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(result.pbData)


def save(key: str) -> Path:
    """Encrypt and save the key for this Windows account, replacing any saved key."""
    key = validate(key)
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = _dpapi(key.encode("utf-16-le"), protect=True).hex()
    temporary = target.with_suffix(".partial")
    temporary.write_text(blob, encoding="ascii")
    os.replace(temporary, target)
    return target


def load() -> str:
    """The saved key, or '' when none is saved or it can't be decrypted here."""
    try:
        raw = path().read_text(encoding="ascii").strip()
        return _dpapi(bytes.fromhex(raw), protect=False).decode("utf-16-le") if raw else ""
    except (OSError, ValueError, UnicodeError, KeyStoreUnavailable):
        return ""


def forget() -> bool:
    try:
        path().unlink()
        return True
    except FileNotFoundError:
        return False


def describe(environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Where a key would come from, without the key."""
    environ = os.environ if environ is None else environ
    saved = path().is_file()
    readable = bool(load()) if saved else False
    source = "environment" if environ.get("CHASEOS_CLOUD_KEY") else ("saved" if readable else "none")
    return {"saved": saved, "readable": readable, "source": source, "file": str(path())}


def check(key: str, *, base_url: str = "", timeout: float = 15) -> dict[str, Any]:
    """Ask ChaseOS Cloud for this key's balance. Free: it reads the account, it runs no model."""
    import urllib.error
    import urllib.request

    from chaser_agent.agent.reasoners import CLOUD_BASE_URL, CLOUD_USER_AGENT

    base = (base_url or os.environ.get("CHASEOS_CLOUD_BASE_URL") or CLOUD_BASE_URL).rstrip("/")
    request = urllib.request.Request(f"{base}/v1/usage", headers={"Authorization": f"Bearer {key}", "User-Agent": CLOUD_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - the owner's gateway
            value = json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return {"ok": False, "refused": True, "reason": "ChaseOS Cloud didn't accept this key. Check it was copied in full."}
        return {"ok": False, "reason": f"ChaseOS Cloud answered with an error ({exc.code}). Try the check again later."}
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError):
        return {"ok": False, "reason": "Couldn't reach ChaseOS Cloud to check the key."}
    credits = value.get("credits") if isinstance(value, dict) else None
    return {"ok": True, "credits": credits if isinstance(credits, (int, float)) else None,
            "plan": value.get("plan") if isinstance(value, dict) else None}
