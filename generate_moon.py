#!/usr/bin/env python3
"""16x16 moonrise-over-hills animation for an LED matrix.

A full moon hanging over two rolling hills, with wisps of cloud drifting
across its face, stars twinkling, and fireflies blinking above the ridgeline.
"""

import math
import os

from pixelart import Canvas, emit_animation, mix

W = H = 16
FRAMES = 32
DELAY_MS = 120

# Cloud drift: one pixel every other frame, so 32 frames carry a wisp exactly
# 16 px -- all the way around the panel and back to where it started.
DRIFT_EVERY = 2

PALETTE = {
    ".": (0x03, 0x05, 0x14),  # sky, zenith
    ",": (0x07, 0x0A, 0x22),  # sky, middle
    ";": (0x15, 0x1D, 0x48),  # sky, moonglow near the horizon
    "1": (0x3A, 0x46, 0x7A),  # star, dim
    "2": (0x8E, 0x9E, 0xC8),  # star, mid
    "3": (0xE8, 0xF2, 0xFF),  # star, bright
    "g": (0x10, 0x14, 0x38),  # moon halo, outer
    "h": (0x1E, 0x26, 0x52),  # moon halo, inner
    "m": (0xF2, 0xEC, 0xC8),  # moon body
    "M": (0xFF, 0xFD, 0xEE),  # moon highlight
    "n": (0xCF, 0xC6, 0x9C),  # maria
    "c": (0x1C, 0x22, 0x48),  # cloud over sky
    "C": (0x9A, 0x96, 0x8A),  # cloud lit from behind by the moon
    "B": (0x0D, 0x13, 0x33),  # far hill
    "b": (0x36, 0x46, 0x86),  # far hill, moonlit rim
    "F": (0x04, 0x06, 0x14),  # near hill
    "f": (0x1E, 0x2A, 0x5C),  # near hill, moonlit rim
    "T": (0x02, 0x03, 0x0C),  # tree
    "t": (0x2A, 0x36, 0x6E),  # tree, moonlit edge
    "y": (0x5E, 0x7A, 0x24),  # firefly, fading
    "Y": (0xCF, 0xF7, 0x62),  # firefly, lit
}

MOON = (10.5, 4.5, 2.8)  # cx, cy, r

# Ridgelines as the topmost lit row per column. Written out rather than
# computed: at 16 px wide, hand-placing each crest beats any curve formula.
FAR_TOP = [12, 11, 10, 10, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14]
NEAR_TOP = [15, 15, 14, 14, 13, 13, 12, 12, 12, 11, 11, 11, 12, 12, 13, 14]

STARS = [(1, 1, 0), (5, 2, 5), (14, 1, 11), (2, 6, 17), (7, 0, 23), (0, 9, 8)]

# Wisps of cloud, as (row, base x, length). Thin and 1 px tall: anything
# thicker stops reading as cloud and starts reading as a second hill. Only
# the first one runs at a height that crosses the disc, so the moon spends
# most of the loop clear and is veiled just as that wisp drifts past.
WISPS = [(3, 2, 4), (7, 8, 5), (9, 13, 3)]

# Firefly: column, row, and the frame its blink starts. Each drifts up a pixel
# partway through so it bobs rather than just switching on.
FLIES = [(6, 11, 2), (12, 10, 14), (3, 8, 22)]
FLY_ON = 7  # frames per blink


def frame(t):
    c = Canvas(PALETTE, W, H)

    # --- sky ---------------------------------------------------------------
    c.rect(0, 0, 15, 3, ".")
    c.rect(0, 4, 15, 8, ",")
    c.rect(0, 9, 15, 15, ";")

    # --- moon halo and moon ------------------------------------------------
    cx, cy, r = MOON
    c.ring(cx, cy, r + 2.4, r + 1.1, "g")
    c.ring(cx, cy, r + 1.1, r, "h")
    c.disc(cx, cy, r, "m")
    c.puts([(9, 3), (10, 3)], "M")          # highlight on the upper limb
    c.puts([(11, 4), (10, 5), (11, 5)], "n")  # maria

    # --- stars -------------------------------------------------------------
    # Each star runs its own slow cycle, offset by phase, so they never
    # pulse in unison.
    for x, y, phase in STARS:
        v = 0.5 - 0.5 * math.cos(2 * math.pi * ((t + phase) % FRAMES) / FRAMES)
        c.put(x, y, "123"[min(2, int(v * 3))])

    # --- clouds ------------------------------------------------------------
    # Drawn over sky and moon alike; a wisp crossing the disc lights up
    # instead of darkening it, which is what sells it as thin cloud.
    shift = (t // DRIFT_EVERY) % W
    for row, base, length in WISPS:
        for i in range(length):
            x = (base + i + shift) % W
            over_moon = (x + 0.5 - cx) ** 2 + (row + 0.5 - cy) ** 2 <= r * r
            c.put(x, row, "C" if over_moon else "c")

    # --- hills -------------------------------------------------------------
    for x in range(W):
        c.rect(x, FAR_TOP[x], x, 15, "B")
        c.put(x, FAR_TOP[x], "b")
    # A lone tree on the far ridge, planted before the near hill is drawn so
    # the foreground can overlap it.
    c.puts([(3, 9), (2, 8), (3, 8), (4, 8), (3, 7)], "T")
    c.puts([(4, 8)], "t")  # the moon is off to the right, so that edge catches it
    for x in range(W):
        c.rect(x, NEAR_TOP[x], x, 15, "F")
        c.put(x, NEAR_TOP[x], "f")

    # --- fireflies ---------------------------------------------------------
    for x, y, start in FLIES:
        age = (t - start) % FRAMES
        if age < FLY_ON:
            bob = 1 if age >= FLY_ON // 2 else 0
            # Bright in the middle of the blink, fading in and out at its ends.
            lit = "Y" if 1 <= age <= FLY_ON - 2 else "y"
            c.put(x, y - bob, lit)

    return c


def frame_palette(t):
    """The halo breathes with the loop; everything else animates as geometry."""
    pal = dict(PALETTE)
    glow = 0.5 - 0.5 * math.cos(2 * math.pi * t / FRAMES)
    pal["g"] = mix(PALETTE[","], PALETTE["g"], 0.55 + 0.45 * glow)
    pal["h"] = mix(PALETTE["g"], PALETTE["h"], 0.55 + 0.45 * glow)
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
    emit_animation("moon16", animate(), here, delay_ms=DELAY_MS)
    still = frame(0)
    still.emit("moon16", here)
    print(still.ascii_art())
