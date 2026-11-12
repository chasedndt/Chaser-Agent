"""A small terminal menu with no dependencies: arrow keys or a letter to choose, Enter to open, Esc or q to go back.

Used by `chaser` (the home menu) and `chaser setup`. When there's no console, `select` returns None and the
caller prints plain text instead, so scripts and pipes never hang on a menu.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

UP, DOWN, ENTER, BACK = "up", "down", "enter", "back"


@dataclass(frozen=True)
class Item:
    key: str        # one letter or digit that picks it straight away
    label: str
    hint: str = ""  # shown dim on the right, e.g. the current value


def read_key() -> str:
    """One key press, as UP, DOWN, ENTER, BACK or the character typed."""
    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return {"H": UP, "P": DOWN}.get(msvcrt.getwch(), "")
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                rest = sys.stdin.read(2) if sys.stdin in __import__("select").select([sys.stdin], [], [], 0.05)[0] else ""
                return {"[A": UP, "[B": DOWN}.get(rest, BACK)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    if ch == "\x03":
        raise KeyboardInterrupt
    if ch in ("\r", "\n"):
        return ENTER
    if ch in ("\x1b", "\x08"):
        return BACK
    return ch


def render(title: str, items: list[Item], chosen: int, header: list[str], paint) -> str:
    lines = [paint(f"  {title}", "head")] + [f"  {line}" for line in header] + [""]
    width = max(len(item.label) for item in items)
    for index, item in enumerate(items):
        pointer = paint("›", "teal") if index == chosen else " "
        label = paint(f"{item.label:<{width}}", "head") if index == chosen else f"{item.label:<{width}}"
        hint = f"  {paint(item.hint, 'dim')}" if item.hint else ""
        lines.append(f"  {pointer} {paint(item.key, 'teal')}  {label}{hint}")
    lines += ["", paint("  ↑↓ move · Enter or a letter to choose · Esc to go back", "dim")]
    return "\n".join(lines)


def select(title: str, items: list[Item], *, header: list[str] | None = None, paint=lambda text, _tone: text,
           interactive: bool = True, start: str | None = None) -> str | None:
    """The chosen item's key, or None for Esc/q or when there's no console to ask."""
    if not interactive or not items:
        return None
    chosen = next((i for i, item in enumerate(items) if item.key == start), 0)
    keys = {item.key.lower(): item.key for item in items}
    while True:
        sys.stdout.write("\033[2J\033[H" + render(title, items, chosen, header or [], paint) + "\n")
        sys.stdout.flush()
        key = read_key()
        if key == UP:
            chosen = (chosen - 1) % len(items)
        elif key == DOWN:
            chosen = (chosen + 1) % len(items)
        elif key == ENTER:
            return items[chosen].key
        elif key == BACK or (key.lower() == "q" and "q" not in keys):
            return None
        elif key.lower() in keys:
            return keys[key.lower()]


def pause(paint=lambda text, _tone: text) -> None:
    """Hold what an action printed until a key is pressed, before the menu redraws over it."""
    sys.stdout.write(paint("\n  Press any key to go back to the menu.", "dim"))
    sys.stdout.flush()
    read_key()
