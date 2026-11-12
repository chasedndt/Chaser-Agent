"""Make the terminal pixel art of Chaser from the approved avatar export, never a redrawing of it.

    python scripts/make_terminal_art.py [--colours 32] [--source EXPORT] [--size N] [--top 0.7]

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
AVATARS = ROOT / "brand/chaser-agent/exports/canon-core/v1.0.0-rc.1/avatar"
SOURCE = AVATARS / "chaser-agent_avatar-transparent_32x32.png"
TARGET = ROOT / "src/chaser_agent/chaser_art.py"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=0, help="pixels across to scale to; 0 keeps the export's own pixels (the default)")
    parser.add_argument("--source", type=Path, default=SOURCE, help="an approved avatar export; the 32x32 one is made for small sizes")
    parser.add_argument("--colours", type=int, default=12)
    parser.add_argument("--top", type=float, default=1.0, help="keep this share of the mascot's height from the top: 0.7 is head and shoulders")
    parser.add_argument("--out", type=Path, default=TARGET)
    args = parser.parse_args()
    source = args.source.resolve()
    image = Image.open(source).convert("RGBA")
    image = image.crop(image.getbbox())  # the mascot, without the empty margin
    if args.top < 1:
        image = image.crop((0, 0, image.width, round(image.height * args.top)))  # a crop of the export, still not a redraw
    if not args.size:
        write(args, source, image.convert("RGB"), image.getchannel("A"), *image.size)
        return
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
    write(args, source, rgb, small.getchannel("A"), args.size, args.size)


def write(args: argparse.Namespace, source: Path, rgb: Image.Image, alpha: Image.Image, width: int, height: int) -> None:
    solid = rgb.quantize(colors=args.colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = solid.getpalette()[: args.colours * 3]
    colours = [f"{palette[i]:02x}{palette[i + 1]:02x}{palette[i + 2]:02x}" for i in range(0, len(palette), 3)]
    rows = []
    for y in range(height):
        line = ""
        for x in range(width):
            line += "." if alpha.getpixel((x, y)) < 128 else "0123456789abcdefghijklmnopqrstuvwxyz"[solid.getpixel((x, y))]
        rows.append(line)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    body = [
        '"""Chaser in terminal pixels, scaled from the approved avatar export. Made by scripts/make_terminal_art.py; don\'t edit by hand."""',
        "",
        f'SOURCE = "{source.relative_to(ROOT).as_posix()}"',
        f'SOURCE_SHA256 = "{digest}"',
        f"CROP_TOP = {args.top}",
        f"PALETTE = {colours!r}",
        "PIXELS = (",
        *[f'    "{row}",' for row in rows],
        ")",
        "",
    ]
    args.out.write_text("\n".join(body), encoding="utf-8", newline="\n")
    print(f"Wrote {args.out}: {width}x{height} pixels, {len(colours)} colours, from {source.name}")


if __name__ == "__main__":
    main()
