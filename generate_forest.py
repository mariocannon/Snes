#!/usr/bin/env python3
"""16x16 wooded forest animation for an LED matrix.

Layered trunks receding into a misty gap of light, a dappled canopy overhead,
and shafts of sun cutting down between the trees. Motes drift up through the
beams, the canopy stirs, and a single leaf falls the height of the panel over
each loop.
"""

import math
import os

from pixelart import Canvas, emit_animation, mix

W = H = 16
FRAMES = 32
DELAY_MS = 110

PALETTE = {
    ".": (0x04, 0x0A, 0x07),  # deepest shade between the trunks
    ",": (0x07, 0x13, 0x0D),  # mist, mid distance
    ";": (0x13, 0x2A, 0x1C),  # mist, lit by the gap
    ":": (0x46, 0x74, 0x42),  # the bright gap itself
    "1": (0x0A, 0x1C, 0x0E),  # canopy, deep
    "2": (0x14, 0x36, 0x1A),  # canopy, mid
    "3": (0x28, 0x58, 0x26),  # canopy, lit
    "4": (0x51, 0x8C, 0x34),  # canopy, sunlit edge
    "S": (0x33, 0x57, 0x2B),  # light shaft
    "s": (0x4C, 0x78, 0x38),  # light shaft, core
    "T": (0x2A, 0x1B, 0x11),  # near trunk
    "t": (0x59, 0x3B, 0x22),  # near trunk, lit edge
    "D": (0x1B, 0x1D, 0x18),  # far trunk, hazed by distance
    "d": (0x33, 0x33, 0x27),  # far trunk, lit edge
    "F": (0x09, 0x11, 0x08),  # forest floor
    "f": (0x20, 0x3A, 0x16),  # moss and undergrowth
    "n": (0x6E, 0x8A, 0x40),  # mote, fading
    "m": (0xD2, 0xEE, 0x86),  # mote, lit
    "L": (0xA8, 0x6A, 0x28),  # falling leaf
}

# Where the light comes from: a gap in the trees, back and slightly right.
GAP = (9.5, 7.0)

# Canopy depth per column -- the lowest row each column's leaves reach. Uneven
# on purpose; a straight canopy edge reads as a ceiling, not as trees.
CANOPY = [4, 3, 2, 3, 4, 3, 2, 1, 2, 3, 2, 3, 4, 3, 4, 5]

# Trunks as (x, width, top, bottom, base char, lit char). Near trunks are warm
# and dark, far ones desaturate toward the mist -- that split is the whole
# depth cue at this size.
TRUNKS = [
    (6, 1, 5, 13, "D", "d"),
    (10, 1, 6, 13, "D", "d"),
    (1, 2, 2, 14, "T", "t"),
    (13, 2, 1, 14, "T", "t"),
]

# Shafts fall from the gap down and to the left, as (x, top row, length),
# stepping one column over per two rows.
SHAFTS = [(11, 2, 11), (14, 3, 9)]

# Undergrowth height per column: the row its fronds reach up to.
UNDER = [14, 13, 14, 15, 13, 14, 14, 13, 15, 14, 13, 14, 15, 13, 14, 14]

# Motes drift up-left through the beams, one step every 4 frames: 8 steps per
# loop, so each is back at its start on the last frame.
MOTES = [(11, 12, 0), (8, 13, 3), (13, 10, 5)]
MIST = ".,;:"


def dapple(x, y, t):
    """Hashed noise on (x, y, t mod FRAMES) so the stir loops with everything."""
    h = (x * 374761393) ^ (y * 668265263) ^ (t * 2246822519)
    h = (h ^ (h >> 15)) & 0x7FFFFFFF
    return h % 100


def frame(t):
    c = Canvas(PALETTE, W, H)

    # --- mist ---------------------------------------------------------------
    # Distance from the gap picks the shade, so the light falls off in every
    # direction instead of banding by row.
    gx, gy = GAP
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - gx, y + 0.5 - gy)
            c.put(x, y, ":" if d < 2.6 else ";" if d < 5.0 else "," if d < 8.0 else ".")

    # --- canopy -------------------------------------------------------------
    # The leaf texture is hashed on position only, so it holds still from
    # frame to frame; hashing it on t as well made the whole canopy boil.
    # Wind is a handful of pixels stirring a step brighter each frame.
    for x in range(W):
        for y in range(CANOPY[x] + 1):
            n = dapple(x, y, 0)
            if y == CANOPY[x]:
                ch = "3" if n < 30 else "2"
            elif n < 12:
                ch = "3"
            elif n < 45:
                ch = "2"
            else:
                ch = "1"
            # Leaves right above the gap catch the light directly.
            if abs(x + 0.5 - gx) < 3 and y >= CANOPY[x] - 1:
                ch = "4" if n < 40 else "3"
            if dapple(x, y, t + 1) < 7:
                ch = {"1": "2", "2": "3", "3": "4", "4": "4"}[ch]
            c.put(x, y, ch)

    # --- light shafts -------------------------------------------------------
    # Two px wide and only over mist, so the trunks and canopy stay solid in
    # front of them. One px of beam disappears into the haze at this size.
    for x0, y0, length in SHAFTS:
        for i in range(length):
            y = y0 + i
            for j, x in enumerate((x0 - i // 2, x0 - i // 2 + 1)):
                if 0 <= x < W and 0 <= y < H and c.grid[y][x] in MIST:
                    c.put(x, y, "s" if j == 0 and i < length - 3 else "S")

    # --- trunks -------------------------------------------------------------
    for x0, width, top, bottom, base, lit in TRUNKS:
        for x in range(x0, x0 + width):
            c.rect(x, top, x, bottom, base)
        # The edge facing the gap catches light; which edge that is depends on
        # which side of the gap the trunk stands. A one-pixel trunk gets no
        # lit edge at all -- it would replace the trunk instead of shading it.
        if width > 1:
            edge = x0 + width - 1 if x0 + width / 2 < gx else x0
            c.rect(edge, top, edge, bottom, lit)

    # --- undergrowth --------------------------------------------------------
    # A ragged line of ferns rather than a flat floor: the uneven top edge is
    # what reads as growth, and the lit tips catch the same light as the gap.
    for x in range(W):
        c.rect(x, UNDER[x], x, 15, "F")
        c.put(x, UNDER[x], "f")
    c.puts([(4, 12), (11, 12)], "F")  # a couple of taller fronds
    c.puts([(4, 11), (11, 11)], "f")

    # --- falling leaf -------------------------------------------------------
    # One row every other frame: exactly the height of the panel per loop.
    ly = t // 2
    lx = 4 + (1 if (t // 4) % 2 else 0)   # a lazy zigzag as it tumbles
    c.put(lx, ly, "L")

    # --- motes --------------------------------------------------------------
    for x0, y0, phase in MOTES:
        step = ((t + phase * 4) // 4) % 8
        # Dim at both ends of the climb, so a mote fades out and back in
        # rather than teleporting when its path wraps.
        faint = step == 0 or step >= 6
        c.put(x0 - step // 2, y0 - step, "n" if faint or (t + phase) % 4 >= 2 else "m")

    return c


def frame_palette(t):
    """The shafts brighten and fade as the canopy moves across the sun."""
    pal = dict(PALETTE)
    breathe = 0.5 - 0.5 * math.cos(2 * math.pi * t / FRAMES)
    pal["S"] = mix(PALETTE[";"], PALETTE["S"], 0.45 + 0.55 * breathe)
    pal["s"] = mix(PALETTE["S"], PALETTE["s"], 0.45 + 0.55 * breathe)
    pal[":"] = mix(PALETTE[";"], PALETTE[":"], 0.6 + 0.4 * breathe)
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
    emit_animation("forest16", animate(), here, delay_ms=DELAY_MS)
    still = frame(0)
    still.emit("forest16", here)
    print(still.ascii_art())
