"""Images and voice as input in the terminal: attach a file, paste from the clipboard, or speak.

Images go to Chaser with the message and are saved and hashed into the session's receipt. Dragging a
file onto Windows Terminal types its path, so a message that contains an image's path attaches it.
Voice uses the offline speech-to-text model (`pip install chaser-agent[voice-input]` and a pinned model
folder set with `chaser voice set FOLDER`); the transcript is a draft you confirm before it's sent.
"""

from __future__ import annotations

import base64
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
MAX_BYTES = 3 * 1024 * 1024
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load_image(path: str | Path) -> dict[str, Any]:
    """{name, media_type, data} for the service, or ValueError saying what's wrong."""
    target = Path(str(path).strip().strip('"').strip("'")).expanduser()
    kind = TYPES.get(target.suffix.lower())
    if kind is None:
        raise ValueError(f"{target.name}: images must be PNG, JPEG, WebP or GIF")
    if not target.is_file():
        raise ValueError(f"{target}: no such file")
    raw = target.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError(f"{target.name} is {len(raw) // 1024 // 1024} MB; the limit is 3 MB")
    return {"name": target.name, "media_type": kind, "data": base64.b64encode(raw).decode("ascii")}


def split_dropped(line: str) -> tuple[str, list[dict[str, Any]]]:
    """Pull image paths a drag-and-drop typed into the message; returns the remaining text and the images."""
    images, kept = [], []
    try:
        words = shlex.split(line, posix=False)
    except ValueError:
        return line, []
    for word in words:
        bare = word.strip('"').strip("'")
        if Path(bare).suffix.lower() in TYPES and os.path.isfile(bare):
            images.append(load_image(bare))
        else:
            kept.append(word)
    return (" ".join(kept) if images else line), images


def clipboard_image() -> dict[str, Any]:
    """The image on the Windows clipboard (a screenshot, a copied picture), saved as PNG."""
    if os.name != "nt":
        raise ValueError("Pasting an image works on Windows; use /image PATH here")
    target = Path(tempfile.gettempdir()) / f"chaser-paste-{os.getpid()}.png"
    script = ("Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; "
              "$i = [System.Windows.Forms.Clipboard]::GetImage(); if ($i -eq $null) { exit 3 }; "
              f"$i.Save('{target}', [System.Drawing.Imaging.ImageFormat]::Png); exit 0")
    code = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", script], capture_output=True, timeout=20,
                          creationflags=NO_WINDOW).returncode
    if code != 0 or not target.is_file():
        raise ValueError("There's no image on the clipboard. Copy a screenshot (Win+Shift+S) or a picture first.")
    try:
        image = load_image(target)
        image["name"] = "pasted.png"
        return image
    finally:
        target.unlink(missing_ok=True)


def voice_ready(settings: dict[str, Any]) -> tuple[bool, str]:
    folder = settings.get("voice_model_dir")
    if not folder:
        return False, "Voice isn't set up. Install it with pip install chaser-agent[voice-input], then: chaser voice set MODEL_FOLDER"
    try:
        import faster_whisper  # noqa: F401
        import sounddevice  # noqa: F401
    except ImportError:
        return False, "The voice packages aren't installed: pip install chaser-agent[voice-input]"
    from chaser_agent.local_stt import verify_local_model

    try:
        verify_local_model(Path(folder))
    except (OSError, ValueError, RuntimeError) as exc:
        return False, f"The voice model in {folder} didn't check out: {exc}"
    return True, folder


def listen(settings: dict[str, Any], seconds: float = 6.0) -> dict[str, Any]:
    """One bounded take from the microphone, transcribed on this computer. Nothing leaves it."""
    from chaser_agent.local_stt import OfflineTranscriber, record_once

    transcriber = OfflineTranscriber(Path(settings["voice_model_dir"]))
    return transcriber.transcribe(record_once(seconds))


def describe(images: list[dict[str, Any]]) -> str:
    return ", ".join(f"{i['name']} ({len(base64.b64decode(i['data'])) // 1024} KB)" for i in images)


_PATHISH = re.compile(r"\.(png|jpe?g|webp|gif)\b", re.I)


def mentions_image(line: str) -> bool:
    return bool(_PATHISH.search(line))
