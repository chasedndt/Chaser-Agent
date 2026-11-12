"""A small terminal menu with no dependencies: arrow keys or a letter to choose, Enter to open, Esc or q to go back.

Used by `chaser` (the home menu) and `chaser setup`. When there's no console, `select` returns None and the
caller prints plain text instead, so scripts and pipes never hang on a menu.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass

UP, DOWN, ENTER, BACK = "up", "down", "enter", "back"


@dataclass(frozen=True)
class Item:
    key: str         # one letter or digit that picks it straight away
    label: str
    hint: str = ""   # shown dim on the right, e.g. the current value
    group: str = ""  # a heading shown above the first item of each group


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


def render(title: str, items: list[Item], chosen: int, header: list[str], paint, *, footer: str = "") -> str:
    lines = ([paint(f"  {title}", "head")] if title else []) + [f"  {line}" for line in header] + [""]
    width = max(len(item.label) for item in items)
    hints = max((len(item.hint) for item in items), default=0)
    row_width = 4 + 1 + 2 + width + (2 + hints if hints else 0) + 2
    group = None
    headings = shutil.get_terminal_size((96, 44)).lines >= len(header) + len(items) + 12
    for index, item in enumerate(items):
        if headings and item.group and item.group != group:
            if group is not None:
                lines.append("")
            lines.append("    " + paint(item.group.upper(), "dim"))
            group = item.group
        hint = f"  {item.hint}" if item.hint else ""
        if index == chosen:
            row = (paint(" ▸ ", "selected_key") + paint(f"{item.key} ", "selected_key") + paint(f" {item.label:<{width}}", "selected")
                   + paint(f"{hint:<{row_width - 7 - width}}", "selected_dim"))
            lines.append("  " + row)
        else:
            lines.append(f"     {paint(item.key, 'key')}  {paint(f'{item.label:<{width}}', 'text')}{paint(hint, 'dim')}")
    keys = footer or "↑↓ move   enter open   a–z jump   esc back"
    lines += ["", "  " + _keys(keys, paint)]
    return "\n".join(lines)


def _keys(text: str, paint) -> str:
    """Footer hints with the keys picked out: 'enter open' shows enter in teal and open dim."""
    out = []
    for part in text.split("   "):
        key, _, words = part.partition(" ")
        out.append(paint(key, "teal") + (" " + paint(words, "dim") if words else ""))
    return "   ".join(out)


def select(title: str, items: list[Item], *, header: list[str] | None = None, paint=lambda text, _tone: text,
           interactive: bool = True, start: str | None = None, footer: str = "") -> str | None:
    """The chosen item's key, or None for Esc/q or when there's no console to ask."""
    if not interactive or not items:
        return None
    chosen = next((i for i, item in enumerate(items) if item.key == start), 0)
    keys = {item.key.lower(): item.key for item in items}
    while True:
        sys.stdout.write("\033[2J\033[H" + render(title, items, chosen, header or [], paint, footer=footer) + "\n")
        sys.stdout.flush()
        key = read_key()
        if key == UP:
            chosen = (chosen - 1) % len(items)
        elif key == DOWN:
            chosen = (chosen + 1) % len(items)
        elif key == ENTER:
            return items[chosen].key
        elif key == "?" and "?" not in keys:
            return "?"
        elif key == BACK or (key.lower() == "q" and "q" not in keys):
            return None
        elif key.lower() in keys:
            return keys[key.lower()]


def pause(paint=lambda text, _tone: text) -> None:
    """Hold what an action printed until a key is pressed, before the menu redraws over it."""
    sys.stdout.write(paint("\n  Press any key to go back to the menu.", "dim"))
    sys.stdout.flush()
    read_key()
