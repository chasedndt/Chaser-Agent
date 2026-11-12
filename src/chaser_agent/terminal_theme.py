"""Chaser's terminal colours: the HUD's palette in 24-bit colour, with a 256-colour fallback.

Every screen paints through `paint(text, tone)`, so a tone means the same thing everywhere: teal is
Chaser and things you can press, amber wants your attention, red is a failure, mute is supporting text.
NO_COLOR or a pipe turns all of it off and the words still read on their own.
"""

from __future__ import annotations

import os
import re

# The HUD's own tokens (console/app.css), so the terminal and the HUD look like one product.
BONE, MUTE, LINE = "f4f1ea", "93a0b5", "2c3a55"
TEAL, EDGE, VIOLET, AMBER, RED = "39e6d2", "4eb7ff", "7c5cff", "f0b45a", "ff4d6d"
SELECTED = "16233a"
SAGE = "8ab8bc"  # the mascot's own body colour

# tone: (foreground, background, bold)
TONES: dict[str, tuple[str | None, str | None, bool]] = {
    "head": (BONE, None, True),
    "text": (BONE, None, False),
    "dim": (MUTE, None, False),
    "info": (MUTE, None, False),
    "line": (LINE, None, False),
    "teal": (TEAL, None, False),
    "key": (TEAL, None, True),
    "edge": (EDGE, None, False),
    "violet": (VIOLET, None, False),
    "sage": (SAGE, None, False),
    "ok": (TEAL, None, False),
    "warn": (AMBER, None, False),
    "fail": (RED, None, False),
    "selected": (BONE, SELECTED, True),
    "selected_dim": (MUTE, SELECTED, False),
    "selected_key": (TEAL, SELECTED, True),
}

_ESCAPE = re.compile(r"\033\[[0-9;]*m")


def truecolor(environ: dict[str, str] | None = None) -> bool:
    """24-bit colour: Windows 10+ consoles and Windows Terminal have it; elsewhere trust COLORTERM."""
    env = os.environ if environ is None else environ
    if env.get("COLORTERM", "").lower() in {"truecolor", "24bit"} or env.get("WT_SESSION"):
        return True
    if env.get("TERM_PROGRAM", "").lower() in {"vscode", "iterm.app", "wezterm", "ghostty", "hyper"}:
        return True
    return os.name == "nt"


def _rgb(value: str) -> tuple[int, int, int]:
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _cube(value: str) -> int:
    """The nearest of the 256 xterm colours, for terminals without 24-bit colour."""
    steps = [0, 95, 135, 175, 215, 255]
    return 16 + sum(min(range(6), key=lambda i: abs(steps[i] - c)) * m for c, m in zip(_rgb(value), (36, 6, 1)))


def code(fg: str | None = None, bg: str | None = None, bold: bool = False, *, full: bool = True) -> str:
    parts = ["1"] if bold else []
    if fg:
        parts.append("38;2;{};{};{}".format(*_rgb(fg)) if full else f"38;5;{_cube(fg)}")
    if bg:
        parts.append("48;2;{};{};{}".format(*_rgb(bg)) if full else f"48;5;{_cube(bg)}")
    return f"\033[{';'.join(parts)}m" if parts else ""


def paint(text: str, tone: str, *, colour: bool = True, full: bool = True) -> str:
    if not colour or not text:
        return text
    fg, bg, bold = TONES[tone]
    return f"{code(fg, bg, bold, full=full)}{text}\033[0m"


def gradient(text: str, stops: tuple[str, ...] = (TEAL, EDGE, VIOLET), *, bold: bool = True, colour: bool = True,
             full: bool = True) -> str:
    """Each letter a step along the stops: the wordmark's teal → blue → violet."""
    if not colour or len(text) < 2:
        return paint(text, "teal", colour=colour, full=full)
    out = []
    for index, letter in enumerate(text):
        at = index / (len(text) - 1) * (len(stops) - 1)
        low = min(int(at), len(stops) - 2)
        mix = at - low
        a, b = _rgb(stops[low]), _rgb(stops[low + 1])
        value = "".join(f"{round(x + (y - x) * mix):02x}" for x, y in zip(a, b))
        out.append(f"{code(value, None, bold, full=full)}{letter}")
    return "".join(out) + "\033[0m"


def wordmark(*, colour: bool = True, full: bool = True) -> str:
    """'Chaser' in Chaser's teal and 'Agent' in bone, both bold: the name as the HUD shows it, without effects."""
    return paint("Chaser", "key", colour=colour, full=full) + paint(" Agent", "head", colour=colour, full=full)


def visible(text: str) -> int:
    """How many columns a painted string takes."""
    return len(_ESCAPE.sub("", text))


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - visible(text))


def box(lines: list[str], width: int, *, title: str = "", colour: bool = True, full: bool = True, tone: str = "line") -> list[str]:
    """Lines inside a rounded frame `width` columns wide, with an optional title set into the top edge."""
    edge = lambda s: paint(s, tone, colour=colour, full=full)  # noqa: E731
    inner = width - 2
    top_fill = inner - 1 - (visible(title) + 2 if title else 0)
    top = edge("╭─") + (f" {title} " if title else "") + edge("─" * max(0, top_fill) + "╮")
    body = [edge("│") + pad(" " + line, inner) + edge("│") for line in lines]
    return [top, *body, edge("╰" + "─" * inner + "╯")]
