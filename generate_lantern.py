#!/usr/bin/env python3
"""16x16 Japanese lantern on black, lit by a guttering candle.

A chochin hanging by its cord: dark caps top and bottom, ribbed paper between
them, a kanji brushed across the middle, and a tassel below. The flame inside
is dim orange, wanders a little, and gutters now and then.

96 frames at 90 ms (8.64 s). The flicker is built from sines whose cycle
counts over the loop are whole numbers, so it reads as irregular but returns
exactly to its starting value -- a candle that never repeats visibly and never
jumps at the wrap.
"""

import math
import os

from pixelart import emit_animation, mix

W = H = 16
FRAMES = 96
DELAY_MS = 90

BLACK = (0x00, 0x00, 0x00)
CAP = (0x1C, 0x11, 0x0A)        # lacquered wood, top and bottom
CORD = (0x2A, 0x1E, 0x14)
RIB = 0.62                      # ribs are the paper, dimmed by this much
INK = (0x4A, 0x12, 0x06)        # the kanji, silhouetted against the glow

PAPER_DIM = (0x38, 0x17, 0x05)  # paper at its lowest ebb
PAPER_HOT = (0xC6, 0x74, 0x20)  # paper right over the flame, at full flare
HALO = (0xFF, 0x8A, 0x20)       # spill onto the black around it

# c cap, p paper, r rib, k kanji, | cord, t tassel
LANTERN = [
    ".......|........",
    ".......|........",
    ".....ccccc......",
    "....ppppppp.....",
    "...ppppppppp....",
    "...rrrrrrrrr....",
    "...ppkkkkkpp....",
    "...ppppkpppp....",
    "...ppkkkkkpp....",
    "...rrrrrrrrr....",
    "...ppppppppp....",
    "....ppppppp.....",
    ".....ccccc......",
    ".......t........",
    "......ttt.......",
    "................",
]

FLAME_X, FLAME_Y = 7.0, 8.2

# Gutters: (frame, depth, half-width). Placed by hand so the flame dips twice
# per loop at uneven intervals rather than on a beat.
GUSTS = [(28, 0.26, 5), (67, 0.34, 7)]


def flame(t):
    """Candle brightness at frame t, in roughly 0.25 - 1.0."""
    ph = 2 * math.pi * t / FRAMES
    v = (0.62
         + 0.15 * math.sin(3 * ph)
         + 0.10 * math.sin(7 * ph + 1.3)
         + 0.07 * math.sin(13 * ph + 2.7)
         + 0.04 * math.sin(23 * ph + 0.6))
    for centre, depth, width in GUSTS:
        d = abs(t - centre)
        d = min(d, FRAMES - d)          # the dip wraps with the loop
        if d < width:
            v -= depth * (1 - d / width) ** 2
    return max(0.25, min(1.0, v))


def frame(t):
    lvl = flame(t)
    # The flame leans about half a pixel as it burns, which is what stops the
    # glow from looking like a lamp on a dimmer.
    fx = FLAME_X + 0.45 * math.sin(2 * math.pi * 5 * t / FRAMES + 0.4)
    fy = FLAME_Y + 0.20 * math.sin(2 * math.pi * 11 * t / FRAMES)

    px = [[BLACK for _ in range(W)] for _ in range(H)]

    # Halo first: spill on the black, strongest close in, and it breathes with
    # the flame so the whole panel pulses rather than just the paper.
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - 7.0) * 0.95, (y - 7.2) * 0.80)
            if d < 8.5:
                px[y][x] = mix(BLACK, HALO, (1 - d / 8.5) ** 2.6 * lvl * 0.30)

    for y in range(H):
        for x in range(W):
            cell = LANTERN[y][x]
            if cell == ".":
                continue
            if cell == "|":
                px[y][x] = CORD
            elif cell == "c":
                px[y][x] = CAP
            elif cell == "t":
                px[y][x] = mix(CAP, PAPER_HOT, 0.35 * lvl)
            else:
                # Paper: brightest over the flame, falling off toward the rim,
                # then scaled by how hard the candle is burning this frame.
                d = math.hypot((x - fx) * 0.85, (y - fy) * 0.70)
                local = max(0.0, 1.0 - d / 6.2)
                glow = lvl * (0.30 + 0.70 * local)
                c = mix(PAPER_DIM, PAPER_HOT, glow)
                if cell == "r":
                    c = mix(BLACK, c, RIB)
                elif cell == "k":
                    c = mix(INK, c, 0.26)   # ink lets a little light through
                px[y][x] = c

    return px


def animate():
    return [frame(t) for t in range(FRAMES)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    frames = animate()
    emit_animation("lantern16", frames, here, delay_ms=DELAY_MS)

    from PIL import Image
    im = Image.new("RGB", (W, H))
    im.putdata([frames[0][y][x] for y in range(H) for x in range(W)])
    im.save(os.path.join(here, "lantern16.png"))
    im.resize((W * 32, H * 32), Image.NEAREST).save(
        os.path.join(here, "lantern16_preview.png"))

    lo = min(flame(t) for t in range(FRAMES))
    hi = max(flame(t) for t in range(FRAMES))
    print("%d frames at %d ms = %.2fs   flame %.2f - %.2f"
          % (len(frames), DELAY_MS, len(frames) * DELAY_MS / 1000, lo, hi))
