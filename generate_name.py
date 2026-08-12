#!/usr/bin/env python3
"""16x16 side-scrolling "THEA & ROMA" banner.

Chunky geometric caps in the style of the reference sheet: a pink body with a
white inline through it and a deeper pink edge behind, on baby blue. Set in
caps because the reference alphabet is caps-only.

The text is laid out once as a wide strip, then each frame is a 16 px window
sliding along it and wrapping, so the scroll is seamless by construction and
the loop is exactly as long as the strip is wide.
"""

import os

from pixelart import Canvas, emit_animation

H = 16
DELAY_MS = 90
TOP = 3          # glyphs are 10 tall, leaving 3 rows above and below
GAP = 1          # columns between letters
SPACE = 4        # columns for a word space
TAIL = 16        # blank columns after the text, so it scrolls clear

# 2px strokes throughout: thick enough that the inline pass has an interior to
# paint, which is what produces the bevel.
FONT = {
    "T": ["########",
          "########",
          "...##...",
          "...##...",
          "...##...",
          "...##...",
          "...##...",
          "...##...",
          "...##...",
          "...##..."],
    "H": ["##....##",
          "##....##",
          "##....##",
          "##....##",
          "########",
          "########",
          "##....##",
          "##....##",
          "##....##",
          "##....##"],
    "E": ["#######",
          "#######",
          "##.....",
          "##.....",
          "######.",
          "######.",
          "##.....",
          "##.....",
          "#######",
          "#######"],
    "A": ["########",
          "########",
          "##....##",
          "##....##",
          "########",
          "########",
          "##....##",
          "##....##",
          "##....##",
          "##....##"],
    # Wider than the letters: at 2px strokes a 9-column ampersand collapses
    # into a blob, and the tail needs room to swing clear to the right.
    "&": ["..#####....",
          ".##...##...",
          ".##...##...",
          "..#####....",
          ".#####.....",
          "##...##...#",
          "##....##.##",
          "##.....###.",
          ".##...####.",
          "..#####..##"],
    "R": ["######..",
          "######..",
          "##..##..",
          "##..##..",
          "######..",
          "######..",
          "##.##...",
          "##..##..",
          "##...##.",
          "##...##."],
    "O": [".######.",
          "########",
          "##....##",
          "##....##",
          "##....##",
          "##....##",
          "##....##",
          "##....##",
          "########",
          ".######."],
    "M": ["##......##",
          "##......##",
          "###....###",
          "####..####",
          "##.####.##",
          "##..##..##",
          "##......##",
          "##......##",
          "##......##",
          "##......##"],
}

TEXT = "THEA & ROMA"

PALETTE = {
    ".": (0x9E, 0xD8, 0xF5),  # baby blue
    "s": (0xC4, 0x2B, 0x82),  # deep pink edge, offset down-right
    "p": (0xFF, 0x62, 0xB0),  # pink body
    "w": (0xFF, 0xFF, 0xFF),  # white inline
}


def strip_width():
    w = 0
    for ch in TEXT:
        w += SPACE if ch == " " else len(FONT[ch][0]) + GAP
    return w + TAIL


def build_strip():
    """The banner laid out full width, as a character grid."""
    width = strip_width()
    mask = [[False] * width for _ in range(H)]

    x = 0
    for ch in TEXT:
        if ch == " ":
            x += SPACE
            continue
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == "#":
                    mask[TOP + gy][x + gx] = True
        x += len(glyph[0]) + GAP

    grid = [["."] * width for _ in range(H)]

    # Edge first, offset down and right, so the letters sit on top of it.
    for y in range(H):
        for x in range(width):
            if mask[y][x] and y + 1 < H and x + 1 < width and not mask[y + 1][x + 1]:
                grid[y + 1][x + 1] = "s"

    # Then the body, white wherever the pixel is not on a top or left edge.
    # With 2px strokes that lands the white on the inside of every stroke.
    for y in range(H):
        for x in range(width):
            if not mask[y][x]:
                continue
            left = x > 0 and mask[y][x - 1]
            above = y > 0 and mask[y - 1][x]
            grid[y][x] = "w" if left and above else "p"

    return grid


def animate(strip):
    width = len(strip[0])
    frames = []
    for t in range(width):
        c = Canvas(PALETTE, 16, H)
        for y in range(H):
            for x in range(16):
                c.put(x, y, strip[y][(t + x) % width])
        frames.append(c.pixels())
    return frames


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    strip = build_strip()
    frames = animate(strip)
    emit_animation("name16", frames, here, delay_ms=DELAY_MS, scale=16)

    still = Canvas(PALETTE, 16, H)
    for y in range(H):
        for x in range(16):
            still.put(x, y, strip[y][x])
    still.emit("name16", here)

    # The whole banner in one image -- not a panel file, but the only way to
    # check letterforms and spacing without scrubbing the animation.
    from PIL import Image
    width = len(strip[0])
    banner = Image.new("RGB", (width, H))
    banner.putdata([PALETTE[strip[y][x]] for y in range(H) for x in range(width)])
    banner.save(os.path.join(here, "name16_strip.png"))
    banner.resize((width * 8, H * 8), Image.NEAREST).save(
        os.path.join(here, "name16_strip_preview.png"))

    print("strip %d px wide -> %d frames at %d ms = %.1fs"
          % (len(strip[0]), len(frames), DELAY_MS, len(frames) * DELAY_MS / 1000))
    print("\n".join("".join(r) for r in strip))
