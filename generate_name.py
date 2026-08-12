#!/usr/bin/env python3
"""16x16 side-scrolling "THEA & ROMA" banner.

Chunky geometric caps in the style of the reference sheet: a pink body with a
white inline through it and a deeper pink edge behind, on baby blue. Set in
caps because the reference alphabet is caps-only.

The text is laid out once as a wide strip, then each frame is a 16 px window
sliding along it and wrapping, so the scroll is seamless by construction and
the loop is exactly as long as the strip is wide.
"""

import math
import os

from pixelart import Canvas, emit_animation, mix

H = 16
DELAY_MS = 90
TOP = 3          # glyphs are 10 tall, leaving 3 rows above and below
GAP = 1          # columns between letters
SPACE = 4        # columns for a word space
TAIL = 15        # blank columns after the text, so it scrolls clear.
                 # One short of the window width on purpose: at 16 a window
                 # lands on flat blue twice running, and the GIF writer merges
                 # the pair, leaving fewer frames than the exported arrays.

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


# --- the sunset that follows the name ---------------------------------------

SKY_FADE = 12    # columns over which baby blue turns into sunset, and back
SUNSET_W = 84    # width of the sunset scene itself

# Sky by row, sampled top to bottom: night at the top down to gold at the
# horizon. Rows below the horizon never show, the land covers them.
SKY = [
    (0x35, 0x18, 0x5C), (0x4C, 0x1B, 0x63), (0x6B, 0x21, 0x69),
    (0x8E, 0x28, 0x6A), (0xB0, 0x30, 0x66), (0xCD, 0x3C, 0x5C),
    (0xE3, 0x50, 0x4E), (0xF0, 0x6A, 0x40), (0xF8, 0x88, 0x33),
    (0xFD, 0xA5, 0x33), (0xFF, 0xBE, 0x3D), (0xFF, 0xD2, 0x52),
    (0xFF, 0xDF, 0x66), (0xFF, 0xE7, 0x78), (0xFF, 0xED, 0x8A),
    (0xFF, 0xF2, 0x9C),
]

SUN = (0xFF, 0xF4, 0xC0)
SUN_RIM = (0xFF, 0xC7, 0x5A)
LAND = (0x24, 0x0C, 0x2C)      # silhouette: everything in front is this
SUN_CX, SUN_CY, SUN_R = 44, 10, 5.4

# Ridge height across the scene, as rows from the bottom. Starts and ends flat
# so the land slides in and out of frame instead of appearing mid-air.
def ridge(i):
    if i < 6 or i > SUNSET_W - 7:
        return 2
    span = (i - 6) / max(1, SUNSET_W - 13)
    hills = (
        2.6 + 1.6 * math.sin(span * 7.0)
        + 0.9 * math.sin(span * 3.1 + 1.2)
        + 0.7 * math.sin(span * 13.0)
    )
    return max(2, min(6, int(round(hills))))


PALM = [
    "..#.#..",
    ".#####.",
    "##.#.##",
    "...#...",
    "...#...",
    "..##...",
    "..#....",
]
PALMS = [14, 66]                 # x offsets within the scene
BIRDS = [(28, 3), (33, 5), (58, 4)]   # small chevrons in the sky


def strip_width():
    w = 0
    for ch in TEXT:
        w += SPACE if ch == " " else len(FONT[ch][0]) + GAP
    return w + TAIL


def text_mask(width):
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
    return mask


def build_strip():
    """The whole banner as RGB rows: name first, then the sunset flowing past.

    Built in RGB rather than palette characters because the sky is a gradient
    in two directions -- down the rows, and across the columns as baby blue
    turns into sunset and back.
    """
    name_w = strip_width()
    sunset_start = name_w + SKY_FADE
    width = sunset_start + SUNSET_W + SKY_FADE + TAIL

    def blend_at(x):
        """0 = baby blue, 1 = full sunset."""
        if x < name_w:
            return 0.0
        if x < sunset_start:
            return (x - name_w) / SKY_FADE
        if x < sunset_start + SUNSET_W:
            return 1.0
        if x < sunset_start + SUNSET_W + SKY_FADE:
            return 1.0 - (x - sunset_start - SUNSET_W) / SKY_FADE
        return 0.0

    strip = [[PALETTE["."]] * width for _ in range(H)]
    for x in range(width):
        b = blend_at(x)
        for y in range(H):
            strip[y][x] = mix(PALETTE["."], SKY[y], b)

    # --- sunset scene, drawn in its own coordinates ------------------------
    for i in range(SUNSET_W):
        x = sunset_start + i
        top = H - ridge(i)

        # Sun, occluded by the land in front of it.
        for y in range(H):
            if math.hypot(i + 0.5 - SUN_CX, y + 0.5 - SUN_CY) <= SUN_R and y < top:
                edge = math.hypot(i + 0.5 - SUN_CX, y + 0.5 - SUN_CY) > SUN_R - 1.2
                strip[y][x] = SUN_RIM if edge else SUN

        for y in range(top, H):
            strip[y][x] = LAND

    for px in PALMS:
        base = H - ridge(px + 3) - 1
        for gy, row in enumerate(PALM):
            for gx, cell in enumerate(row):
                if cell != "#":
                    continue
                x, y = sunset_start + px + gx, base - len(PALM) + 1 + gy
                if 0 <= y < H and sunset_start <= x < sunset_start + SUNSET_W:
                    strip[y][x] = LAND

    for bx, by in BIRDS:
        for dx, dy in ((0, 0), (1, -1), (2, 0)):
            x, y = sunset_start + bx + dx, by + dy
            if 0 <= y < H:
                strip[y][x] = LAND

    # --- the name, painted over the baby blue ------------------------------
    mask = text_mask(width)
    for y in range(H):
        for x in range(width):
            if mask[y][x] and y + 1 < H and x + 1 < width and not mask[y + 1][x + 1]:
                strip[y + 1][x + 1] = PALETTE["s"]
    for y in range(H):
        for x in range(width):
            if not mask[y][x]:
                continue
            left = x > 0 and mask[y][x - 1]
            above = y > 0 and mask[y - 1][x]
            strip[y][x] = PALETTE["w"] if left and above else PALETTE["p"]

    return strip


def animate(strip):
    width = len(strip[0])
    return [[[strip[y][(t + x) % width] for x in range(16)] for y in range(H)]
            for t in range(width)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    strip = build_strip()
    frames = animate(strip)
    emit_animation("name16", frames, here, delay_ms=DELAY_MS, scale=16)

    # Frame 0 as the still.
    from PIL import Image
    first = Image.new("RGB", (16, H))
    first.putdata([frames[0][y][x] for y in range(H) for x in range(16)])
    first.save(os.path.join(here, "name16.png"))
    first.resize((16 * 32, H * 32), Image.NEAREST).save(
        os.path.join(here, "name16_preview.png"))

    # The whole banner in one image -- not a panel file, but the only way to
    # check letterforms, spacing and the sunset without scrubbing frames.
    width = len(strip[0])
    banner = Image.new("RGB", (width, H))
    banner.putdata([strip[y][x] for y in range(H) for x in range(width)])
    banner.save(os.path.join(here, "name16_strip.png"))
    banner.resize((width * 8, H * 8), Image.NEAREST).save(
        os.path.join(here, "name16_strip_preview.png"))

    print("strip %d px wide -> %d frames at %d ms = %.1fs"
          % (len(strip[0]), len(frames), DELAY_MS, len(frames) * DELAY_MS / 1000))
