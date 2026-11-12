"""The global keys that stop Chaser or take over from it: checking a chord and whether it's free.

Chosen on 11 November 2026 (docs/01_Product/Chaser-Agent-Mini-Player-HUD.md, option A). Nothing in
this version holds them: they matter once Chaser controls the mouse and keyboard. Until then this
only says whether each chord is free, by registering it for a moment and releasing it.
"""

from __future__ import annotations

import os
from typing import Any

NAMES = {"stop": "Stop", "stop_fallback": "Stop on a laptop with no Pause key", "take_over": "Take over"}
MODIFIERS = {"ctrl": 0x0002, "alt": 0x0001, "shift": 0x0004}
MOD_NOREPEAT = 0x4000
KEYS = {"pause": 0x13, "home": 0x24, "end": 0x23, "insert": 0x2D, "delete": 0x2E, "pageup": 0x21, "pagedown": 0x22,
        **{chr(c).lower(): c for c in range(ord("A"), ord("Z") + 1)}, **{str(d): 0x30 + d for d in range(10)},
        **{f"f{n}": 0x6F + n for n in range(1, 12)}}  # F12 is the debugger's
LABELS = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "pause": "Pause", "home": "Home", "end": "End", "insert": "Insert",
          "delete": "Delete", "pageup": "PageUp", "pagedown": "PageDown"}
# Windows, Remote Desktop and accessibility already use these, or they're too easy to press by accident.
RULED_OUT = {
    frozenset({"ctrl", "alt"}) | {"delete"}: "Windows uses Ctrl+Alt+Delete.",
    frozenset({"ctrl", "alt"}) | {"insert"}: "Windows uses Ctrl+Alt+Insert.",
    frozenset({"ctrl", "alt"}) | {"end"}: "Remote Desktop uses Ctrl+Alt+End.",
}


def parse(chord: str) -> tuple[frozenset[str], str]:
    """'Ctrl+Alt+Pause' -> ({'ctrl', 'alt'}, 'pause'). ValueError says why a chord can't be used."""
    parts = [part.strip().lower() for part in (chord or "").replace(" ", "").split("+") if part.strip()]
    if not parts:
        raise ValueError("Press a key combination.")
    *mods, key = parts
    mods_set = frozenset("ctrl" if m == "control" else m for m in mods)
    if "win" in mods_set or "meta" in mods_set:
        raise ValueError("Windows keeps the Windows key for itself.")
    if not mods_set <= set(MODIFIERS) or len(mods_set) != len(mods):
        raise ValueError("Use Ctrl, Alt and Shift with one other key.")
    if key not in KEYS:
        raise ValueError("Use a letter, a number, F1 to F11, Pause, Home, End, Insert, Delete, PageUp or PageDown.")
    if not {"ctrl", "alt"} <= mods_set:
        raise ValueError("Include Ctrl and Alt, so the keys can't be pressed by accident.")
    if mods_set == {"ctrl", "alt"} and len(key) == 1:
        raise ValueError("On many keyboards Ctrl+Alt with a letter or number types a character (AltGr). Add Shift.")
    reason = RULED_OUT.get(mods_set | {key})
    if reason:
        raise ValueError(reason)
    return mods_set, key


def label(chord: str) -> str:
    mods, key = parse(chord)
    order = [m for m in ("ctrl", "alt", "shift") if m in mods]
    return "+".join([LABELS[m] for m in order] + [LABELS.get(key, key.upper())])


def probe(chord: str) -> str:
    """'free', 'taken' (another app holds it) or 'unknown' (not Windows). Holds it for a moment only."""
    mods, key = parse(chord)
    if os.name != "nt":
        return "unknown"
    import ctypes

    user32 = ctypes.windll.user32
    flags = sum(MODIFIERS[m] for m in mods) | MOD_NOREPEAT
    hotkey_id = 0xB7C1
    if not user32.RegisterHotKey(None, hotkey_id, flags, KEYS[key]):
        return "taken"
    user32.UnregisterHotKey(None, hotkey_id)
    return "free"


def overview(chosen: dict[str, str]) -> list[dict[str, Any]]:
    """One row per shortcut, as the HUD's Shortcuts panel and `chaser shortcuts` show it."""
    rows = []
    for name, title in NAMES.items():
        chord = chosen.get(name, "")
        try:
            state = probe(chord)
            keys = label(chord).split("+")
            problem = None
        except ValueError as exc:
            state, keys, problem = "invalid", [], str(exc)
        rows.append({"name": name, "title": title, "chord": chord, "keys": keys, "state": state, "problem": problem})
    return rows


def check_choice(name: str, chord: str, chosen: dict[str, str]) -> str:
    """The cleaned chord if it can be used for this shortcut. ValueError otherwise."""
    if name not in NAMES:
        raise ValueError("Unknown shortcut.")
    clean = label(chord)
    for other, value in chosen.items():
        if other != name and value and label(value) == clean:
            raise ValueError(f"{NAMES[other]} already uses {clean}.")
    if probe(clean) == "taken":
        raise ValueError(f"Another app already uses {clean}. Pick another.")
    return clean
