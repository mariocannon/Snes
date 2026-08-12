#!/usr/bin/env python3
"""16x16 Eye of Sauron animation for an LED matrix.

The lidless eye wreathed in flame above the dark spire of Barad-dur. Fire
licks around the rim, the glow behind it swells, and the slit pupil sweeps
left and right, searching.
"""

import math
import os

from pixelart import Canvas, emit_animation, mix

W = H = 16
FRAMES = 24
DELAY_MS = 100

PALETTE = {
    ".": (0x07, 0x02, 0x02),  # void
    ",": (0x26, 0x06, 0x02),  # outer glow
    ";": (0x4E, 0x0D, 0x02),  # inner glow
    "1": (0x8C, 0x14, 0x04),  # flame, deep
    "2": (0xD6, 0x3E, 0x06),  # flame, mid
    "3": (0xFF, 0x8A, 0x10),  # flame, bright
    "4": (0xFF, 0xC9, 0x3E),  # eye, molten
    "5": (0xFF, 0xF2, 0xB4),  # eye, white-hot around the slit
    "k": (0x09, 0x01, 0x00),  # pupil
    "T": (0x0D, 0x0A, 0x10),  # tower
    "t": (0x3C, 0x1A, 0x0E),  # tower, firelit edge
}

EYE = (8.0, 7.0, 6.0, 3.4)  # cx, cy, half-width, half-height

# Barad-dur below, stepping wider as it falls away: (left x, right x, row).
TOWER = [(7, 8, 11), (6, 9, 12), (6, 9, 13), (5, 10, 14), (4, 11, 15)]

# Pupil sweep across the loop -- the eye searching rather than staring. Whole
# pixels only; there is no room for a smooth pan at this size.
SWEEP = [0, 0, 1, 1, 1, 0, 0, -1, -1, -1, -1, 0, 0, 1, 1, 1, 1, 0, 0, -1, -1, -1, 0, 0]


def noise(x, y, t):
    h = (x * 374761393) ^ (y * 668265263) ^ (t * 2246822519)
    h = (h ^ (h >> 15)) & 0x7FFFFFFF
    return h % 100


def frame(t):
    c = Canvas(PALETTE, W, H)
    cx, cy, rx, ry = EYE

    def er(x, y):
        """Normalized radius in the eye's ellipse: 1.0 is the rim."""
        return math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)

    # The eye is a lens -- the overlap of two circles -- not an ellipse. That
    # is what gives it points at the corners; an ellipse just reads as a blob.
    lens_r = (rx * rx + ry * ry) / (2 * ry)
    lens_off = lens_r - ry

    def in_eye(x, y):
        for oy in (cy - lens_off, cy + lens_off):
            if math.hypot(x + 0.5 - cx, y + 0.5 - oy) > lens_r:
                return False
        return True

    # --- glow ---------------------------------------------------------------
    for y in range(H):
        for x in range(W):
            r = er(x, y)
            c.put(x, y, ";" if r < 1.5 else "," if r < 2.1 else ".")

    # --- the eye ------------------------------------------------------------
    # Banded by ellipse radius inside the lens: molten at the center, cooling
    # to deep red at the rim, which the flame pass below then leaves ragged.
    for y in range(H):
        for x in range(W):
            if in_eye(x, y):
                r = er(x, y)
                c.put(x, y, "4" if r < 0.42 else "3" if r < 0.70 else "2")

    # --- flame --------------------------------------------------------------
    # Fire is what makes the eye read as an eye rather than a lozenge: the rim
    # has to be uneven, and it has to move. Tongues reach further above the
    # eye than below, the way flame does.
    for y in range(H):
        for x in range(W):
            if in_eye(x, y):
                continue
            r = er(x, y)
            reach = 1.5 if y + 0.5 < cy else 1.2
            if r < reach:
                n = noise(x, y, t)
                lick = min(1.0, max(0.0, (r - 0.9) / (reach - 0.9)))
                if n > lick * 110:
                    c.put(x, y, "1" if lick > 0.6 else "2" if lick > 0.3 else "3")

    # --- pupil --------------------------------------------------------------
    # One pixel wide, flanked by white-hot iris. Two px of black swallowed the
    # eye at this size; the bright flanks are what make the slit read.
    px = 8 + SWEEP[t % len(SWEEP)]
    for y in range(H):
        if in_eye(px, y) and abs(y + 0.5 - cy) < ry - 0.4:
            c.put(px, y, "k")
            # Only the middle of the slit gets white-hot flanks -- running
            # them the full height turned the iris into a bright capsule.
            if abs(y + 0.5 - cy) < ry * 0.62:
                for side in (px - 1, px + 1):
                    if c.grid[y][side] in "234":
                        c.put(side, y, "5")

    # --- Barad-dur ----------------------------------------------------------
    # Firelight catches the top and outer edges of each tier; unlit, the tower
    # is just a black hole under the eye.
    for left, right, row in TOWER:
        c.rect(left, row, right, row, "T")
        c.put(left, row, "t")
        c.put(right, row, "t")

    return c


def frame_palette(t):
    """The glow behind the eye swells and falls back over the loop."""
    pal = dict(PALETTE)
    breathe = 0.5 - 0.5 * math.cos(2 * math.pi * t / FRAMES)
    pal[";"] = mix(PALETTE[","], PALETTE[";"], 0.4 + 0.6 * breathe)
    pal[","] = mix(PALETTE["."], PALETTE[","], 0.4 + 0.6 * breathe)
    return pal


def animate():
    frames = []
    for t in range(FRAMES):
        c = frame(t)
        c.palette = frame_palette(t)
        frames.append(c.pixels())
    return frames


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    emit_animation("eye16", animate(), here, delay_ms=DELAY_MS)
    still = frame(0)
    still.emit("eye16", here)
    print(still.ascii_art())
