#!/usr/bin/env python3
"""Re-emit a piece in whatever layout a particular panel expects.

The art is always authored row-major from the top-left. Panels disagree: some
start in another corner, some are rotated, and most DIY 16x16 boards are wired
serpentine, where every other row runs backwards. Display probe16.png to find
out which, then run this to bake the correction into the file.

    python3 panelfit.py tie16 --serpentine
    python3 panelfit.py moon16 --rotate 180 --flip-x
    python3 panelfit.py eye16 --serpentine --rotate 90 --out panel

Writes <name>_fit.png (and _fit.gif when the piece is animated) plus raw
binaries: RGB888 as 3 bytes per pixel, RGB565 as 2 bytes big-endian, frames
concatenated in order.
"""

import argparse
import os

from PIL import Image, ImageSequence


def rotate(px, deg):
    for _ in range((deg // 90) % 4):
        px = [list(r) for r in zip(*px[::-1])]
    return px


def flip_x(px):
    return [list(reversed(r)) for r in px]


def flip_y(px):
    return list(reversed([list(r) for r in px]))


def serpentine(px, first_reversed_row=1):
    """Pre-reverse alternate rows so a zigzag-wired panel unzigzags them."""
    out = []
    for y, row in enumerate(px):
        out.append(list(reversed(row)) if y % 2 == first_reversed_row % 2 else list(row))
    return out


def transform(px, args):
    if args.rotate:
        px = rotate(px, args.rotate)
    if args.flip_x:
        px = flip_x(px)
    if args.flip_y:
        px = flip_y(px)
    # Serpentine last: it describes the wiring of the final scan order, so it
    # has to be applied after any rotation has settled which way rows run.
    if args.serpentine:
        px = serpentine(px, 0 if args.serpentine_even else 1)
    return px


def to_pixels(img):
    img = img.convert("RGB")
    w, h = img.size
    # get_flattened_data() on Pillow 12+, getdata() before it.
    grab = getattr(img, "get_flattened_data", img.getdata)
    data = list(grab())
    return [list(data[y * w:(y + 1) * w]) for y in range(h)]


def to_image(px):
    h, w = len(px), len(px[0])
    img = Image.new("RGB", (w, h))
    img.putdata([p for row in px for p in row])
    return img


def write_bins(frames, base):
    with open(base + "_rgb888.bin", "wb") as f:
        for fr in frames:
            for row in fr:
                for r, g, b in row:
                    f.write(bytes((r, g, b)))
    with open(base + "_rgb565.bin", "wb") as f:
        for fr in frames:
            for row in fr:
                for r, g, b in row:
                    v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                    f.write(bytes((v >> 8, v & 0xFF)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("name", help="piece name, e.g. tie16")
    ap.add_argument("--rotate", type=int, default=0, choices=(0, 90, 180, 270),
                    help="clockwise rotation to apply")
    ap.add_argument("--flip-x", action="store_true", help="mirror left-right")
    ap.add_argument("--flip-y", action="store_true", help="mirror top-bottom")
    ap.add_argument("--serpentine", action="store_true",
                    help="pre-reverse alternate rows for zigzag wiring")
    ap.add_argument("--serpentine-even", action="store_true",
                    help="zigzag starts on row 0 rather than row 1")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--src", default=".", help="directory holding the piece")
    args = ap.parse_args()
    if args.serpentine_even:
        args.serpentine = True
    os.makedirs(args.out, exist_ok=True)
    base = os.path.join(args.out, args.name + "_fit")

    still = os.path.join(args.src, args.name + ".png")
    anim = os.path.join(args.src, args.name + "_anim.gif")
    if not os.path.exists(still):
        raise SystemExit("no such piece: " + still)

    to_image(transform(to_pixels(Image.open(still)), args)).save(base + ".png")

    if os.path.exists(anim):
        src = Image.open(anim)
        delay = src.info.get("duration", 100)
        frames = [transform(to_pixels(f), args) for f in ImageSequence.Iterator(src)]
        imgs = [to_image(f).convert("P", palette=Image.ADAPTIVE) for f in frames]
        imgs[0].save(base + ".gif", save_all=True, append_images=imgs[1:],
                     duration=delay, loop=0, disposal=2, optimize=False)
        write_bins(frames, base)
        print("wrote %s.png, %s.gif (%d frames) and raw .bin pair"
              % (base, base, len(frames)))
    else:
        write_bins([transform(to_pixels(Image.open(still)), args)], base)
        print("wrote %s.png and raw .bin pair" % base)


if __name__ == "__main__":
    main()
