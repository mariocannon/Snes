#!/usr/bin/env python3
"""16x16 skull that cycles colour, then dissolves away as falling code.

A 30 second loop in four movements:

    0.0 - 18.0s  the skull sweeps twice round the colour wheel
   18.0 - 22.8s  matrix rain sweeps down; every pixel the rain passes stops
                 being skull and falls away as code
   22.8 - 25.2s  rain only, the skull gone
   25.2 - 30.0s  a second sweep, the skull re-forming in its wake

The rebuild is what lets it loop: the last frame lands exactly on the first,
so the panel can run it forever without a seam.
"""

import colorsys
import os
import random

from pixelart import Canvas, emit_animation, mix

W = H = 16
FRAMES = 250
DELAY_MS = 120  # 250 x 120ms = 30.0s exactly

DISSOLVE_START = 150
REBUILD_START = 210
FADE_OUT = 12          # frames of rain fade at the very end
DROP_SPEED = 0.7       # rows per frame for a sweeping drop
TRAIL = 6              # length of a drop's tail

# '#' skull, '.' empty.
MASK = [
    "................",
    "....########....",
    "..############..",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    "..############..",
    "..############..",
    "...##########...",
    "....########....",
    "....########....",
    ".....######.....",
    "................",
]

# Hollows, cut only where skull still remains: deep sockets, a nasal cavity,
# and a row of teeth made of gaps rather than drawn lines.
SOCKETS = [(3, 5), (4, 5), (5, 5), (3, 6), (4, 6), (5, 6), (4, 7), (5, 7),
           (10, 5), (11, 5), (12, 5), (10, 6), (11, 6), (12, 6), (10, 7), (11, 7)]
NOSE = [(7, 9), (8, 9), (7, 10), (8, 10)]
MOUTH = [(5, 12), (6, 12), (7, 12), (8, 12), (9, 12), (10, 12)]
TEETH = [(5, 13), (7, 13), (9, 13), (6, 14), (8, 14), (10, 14)]
HOLLOWS = SOCKETS + NOSE + MOUTH + TEETH

BASE = {
    ".": (0x04, 0x04, 0x08),  # background
    "k": (0x02, 0x02, 0x05),  # sockets, nose, mouth
}

# Rain ramp: head first, then the tail cooling behind it.
RAIN = ["A", "B", "C", "D", "E", "F"]
RAIN_RGB = [
    (0xDA, 0xFF, 0xE2),
    (0x76, 0xFF, 0x94),
    (0x2E, 0xEE, 0x5A),
    (0x13, 0xC0, 0x3A),
    (0x0A, 0x7C, 0x26),
    (0x05, 0x42, 0x14),
]


def stagger(seed=8675309):
    """Per-column head starts, so the rain arrives as a ragged front."""
    rng = random.Random(seed)
    return ([rng.randrange(15) for _ in range(W)],
            [rng.randrange(15) for _ in range(W)],
            [rng.randrange(32) for _ in range(W)])


DISSOLVE_DELAY, REBUILD_DELAY, AMBIENT_PHASE = stagger()


def flicker(x, y, t):
    """Hashed per-pixel noise, so glyphs change character as they fall."""
    h = (x * 374761393) ^ (y * 668265263) ^ (t * 2246822519)
    return ((h ^ (h >> 15)) & 0x7FFFFFFF) % 100


def head_row(x, t, start, delays):
    """How far this column's sweeping drop has fallen, in rows."""
    return (t - start - delays[x]) * DROP_SPEED


def skull_present(x, y, t):
    if t < DISSOLVE_START:
        return True
    if t < REBUILD_START:
        return head_row(x, t, DISSOLVE_START, DISSOLVE_DELAY) <= y
    return head_row(x, t, REBUILD_START, REBUILD_DELAY) > y


def palette(t):
    """Skull colour for this frame, plus the rain ramp at its current fade."""
    pal = dict(BASE)
    hue = (2 * t / FRAMES) % 1.0  # two full turns of the wheel per loop
    pal["H"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.80, 0.88))
    pal["h"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.40, 1.00))
    pal[":"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.90, 0.17))

    # The rain has to be gone by the last frame or it pops on the loop.
    fade = 1.0
    if t >= FRAMES - FADE_OUT:
        fade = (FRAMES - 1 - t) / FADE_OUT
    for ch, rgb in zip(RAIN, RAIN_RGB):
        pal[ch] = mix(BASE["."], rgb, fade)
    return pal


def frame(t):
    c = Canvas(palette(t), W, H)
    present = [[MASK[y][x] == "#" and skull_present(x, y, t)
                for x in range(W)] for y in range(H)]

    # Backglow follows whatever skull is left, rather than the original
    # outline, so the halo dissolves along with it.
    for y in range(H):
        for x in range(W):
            if present[y][x]:
                continue
            if any(0 <= x + dx < W and 0 <= y + dy < H and present[y + dy][x + dx]
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                c.put(x, y, ":")

    for y in range(H):
        for x in range(W):
            if present[y][x]:
                c.put(x, y, "H")

    # Rim light on the topmost remaining pixel of each column.
    for x in range(W):
        for y in range(H):
            if present[y][x]:
                c.put(x, y, "h")
                break

    for x, y in HOLLOWS:
        if present[y][x]:
            c.put(x, y, "k")

    # --- rain ---------------------------------------------------------------
    if t >= DISSOLVE_START:
        # Ambient columns, so the gap between the two sweeps is not empty.
        for x in range(W):
            head = int(((t - DISSOLVE_START) * DROP_SPEED + AMBIENT_PHASE[x]) % 34) - 2
            for i in range(TRAIL):
                y = head - i
                if 0 <= y < H:
                    level = min(i + 1, len(RAIN) - 1)
                    if level > 1 and flicker(x, y, t) < 14:
                        level -= 1   # a glyph changing character
                    c.put(x, y, RAIN[level])

        # The sweep that eats the skull: tail behind it covers what it removed.
        for x in range(W):
            head = int(head_row(x, t, DISSOLVE_START, DISSOLVE_DELAY))
            if t < REBUILD_START and -1 <= head < H + TRAIL:
                for i in range(TRAIL):
                    y = head - i
                    if 0 <= y < H:
                        c.put(x, y, RAIN[min(i, len(RAIN) - 1)])

        # The rebuilding sweep: tail runs ahead of it instead, so the code is
        # consumed into the skull rather than painted over it.
        for x in range(W):
            head = int(head_row(x, t, REBUILD_START, REBUILD_DELAY))
            if t >= REBUILD_START and -1 <= head < H:
                for i in range(TRAIL):
                    y = head + i
                    if 0 <= y < H and not present[y][x]:
                        c.put(x, y, RAIN[min(i, len(RAIN) - 1)])

    return c


def animate():
    return [frame(t).pixels() for t in range(FRAMES)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    emit_animation("skull16", animate(), here, delay_ms=DELAY_MS, scale=16)
    still = frame(0)
    still.emit("skull16", here)
    print(still.ascii_art())
