"""Draw Chaser in the terminal: the approved avatar as half-block pixels, with words beside it.

Two pixels share one character: ▀ with the top pixel as its colour and the bottom one as its background.
It needs a terminal with 24-bit colour and Unicode (Windows Terminal, recent PowerShell and conhost,
most others). It's left out when colour is off (NO_COLOR, a pipe), when CHASER_NO_ART is set, or when
the window is too narrow, so the words always come through.
"""

from __future__ import annotations

import os
import shutil

from chaser_agent import chaser_art

UPPER, LOWER = "▀", "▄"
MIN_COLUMNS = 72


def _rgb(index: str) -> str | None:
    if index == ".":
        return None
    value = chaser_art.PALETTE[int(index, 36)]
    return f"{int(value[0:2], 16)};{int(value[2:4], 16)};{int(value[4:6], 16)}"


def mascot() -> list[str]:
    """Chaser as lines of coloured half blocks, each len(PIXELS[0]) characters wide on screen."""
    rows = list(chaser_art.PIXELS)
    if len(rows) % 2:
        rows.append("." * len(rows[0]))
    lines = []
    for top, bottom in zip(rows[::2], rows[1::2]):
        cells = []
        for a, b in zip(top, bottom):
            up, down = _rgb(a), _rgb(b)
            if up and down:
                cells.append(f"\033[38;2;{up}m\033[48;2;{down}m{UPPER}\033[0m")
            elif up:
                cells.append(f"\033[38;2;{up}m{UPPER}\033[0m")
            elif down:
                cells.append(f"\033[38;2;{down}m{LOWER}\033[0m")
            else:
                cells.append(" ")
        lines.append("".join(cells))
    return lines


def width() -> int:
    return len(chaser_art.PIXELS[0])


def enabled(colour: bool) -> bool:
    if not colour or os.environ.get("CHASER_NO_ART"):
        return False
    return shutil.get_terminal_size((80, 24)).columns >= MIN_COLUMNS


def beside(words: list[str], colour: bool, gap: int = 3) -> list[str]:
    """Chaser on the left and these lines on the right, centred against it. Just the words without art."""
    if not enabled(colour):
        return list(words)
    art = mascot()
    top = max(0, (len(art) - len(words)) // 2)
    lines = []
    for index in range(max(len(art), top + len(words))):
        left = art[index] if index < len(art) else " " * width()
        right = words[index - top] if 0 <= index - top < len(words) else ""
        lines.append(f"{left}{' ' * gap}{right}".rstrip())
    return lines
