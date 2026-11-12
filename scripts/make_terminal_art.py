"""Make the terminal pixel art of Chaser from the approved avatar export, never a redrawing of it.

    python scripts/make_terminal_art.py [--size 24] [--colours 12]

The brand rule (brand/chaser-agent/README.md) is to consume an explicitly versioned approved export.
So this scales the canon-core avatar down, keeps its own colours (reduced to a small palette so it
reads as pixels), and writes src/chaser_agent/chaser_art.py with the source path, version and hash.
Needs Pillow, which only this script uses; the art it writes needs nothing.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/avatar/chaser-agent_avatar-transparent_1024x1024.png"
TARGET = ROOT / "src/chaser_agent/chaser_art.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=24, help="pixels across; the art is this many columns and half as many rows")
    parser.add_argument("--colours", type=int, default=12)
    args = parser.parse_args()
    image = Image.open(SOURCE).convert("RGBA")
    image = image.crop(image.getbbox())  # the mascot, without the empty margin
    side = max(image.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(image, ((side - image.width) // 2, side - image.height))  # sits on the bottom edge, as in the export
    small = square.resize((args.size, args.size), Image.Resampling.BOX)
    # Averaging loses the face's thin white constellation, Chaser's signature. Where a block of the dark
    # screen holds bright pixels, keep the bright colour instead: a feature-preserving downscale, not a redraw.
    block = side / args.size
    rgb, pixels = small.convert("RGB"), square.load()
    for y in range(args.size):
        for x in range(args.size):
            r, g, b = rgb.getpixel((x, y))
            if (r + g + b) / 3 > 70:
                continue
            brightest = max(((pixels[i, j][:3]) for j in range(int(y * block), int((y + 1) * block)) for i in range(int(x * block), int((x + 1) * block))
                             if pixels[i, j][3] > 200), key=sum, default=(0, 0, 0))
            if sum(brightest) / 3 > 200:
                rgb.putpixel((x, y), brightest)
    alpha = small.getchannel("A")
    solid = rgb.quantize(colors=args.colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = solid.getpalette()[: args.colours * 3]
    colours = [f"{palette[i]:02x}{palette[i + 1]:02x}{palette[i + 2]:02x}" for i in range(0, len(palette), 3)]
    rows = []
    for y in range(args.size):
        line = ""
        for x in range(args.size):
            line += "." if alpha.getpixel((x, y)) < 128 else "0123456789abcdefghijklmnopqrstuvwxyz"[solid.getpixel((x, y))]
        rows.append(line)
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    body = [
        '"""Chaser in terminal pixels, scaled from the approved avatar export. Made by scripts/make_terminal_art.py; don\'t edit by hand."""',
        "",
        f'SOURCE = "{SOURCE.relative_to(ROOT).as_posix()}"',
        f'SOURCE_SHA256 = "{digest}"',
        f"PALETTE = {colours!r}",
        "PIXELS = (",
        *[f'    "{row}",' for row in rows],
        ")",
        "",
    ]
    TARGET.write_text("\n".join(body), encoding="utf-8", newline="\n")
    print(f"Wrote {TARGET.relative_to(ROOT)}: {args.size}x{args.size} pixels, {len(colours)} colours, from {SOURCE.name}")


if __name__ == "__main__":
    main()
