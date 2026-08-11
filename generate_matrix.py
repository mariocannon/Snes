#!/usr/bin/env python3
"""16x16 Matrix digital-rain animation for an LED matrix.

Sixteen columns of falling code: a white-hot leader pixel with a green trail
fading out behind it, plus the glyph-flicker of characters changing mid-fall.

Unlike the other pieces the grid is procedural -- each frame is drawn from the
column state at time t rather than authored pixel by pixel -- but it still
lands on the same Canvas and the same exporters.
"""

import os
import random

from pixelart import Canvas, emit_animation

W = H = 16
FRAMES = 32
DELAY_MS = 80

# A column's head travels CYCLE rows before repeating. At twice the screen
# height, every column spends about half the loop off-screen, which is what
# keeps the rain from looking like 16 synchronized elevators.
CYCLE = 32

# Head, then the trail fading behind it. The ramp is deliberately steep for
# the first two steps -- on an LED panel a gentle fade off the leader just
# reads as a fat blur instead of a falling glyph.
PALETTE = {
    ".": (0x00, 0x08, 0x03),  # background, near-black green
    "H": (0xD6, 0xFF, 0xDE),  # leader glyph, blown out
    "1": (0x78, 0xFF, 0x96),
    "2": (0x30, 0xF0, 0x5C),
    "3": (0x14, 0xC4, 0x3C),
    "4": (0x0C, 0x8E, 0x2A),
    "5": (0x07, 0x5C, 0x1C),
    "6": (0x04, 0x36, 0x12),
    "7": (0x02, 0x1C, 0x09),
}
TRAIL = ["H", "1", "2", "3", "4", "5", "6", "7"]


def columns(seed=20260811):
    """Per-column speed, phase and trail length.

    Speeds are whole rows per frame and CYCLE is a multiple of FRAMES, so
    every column returns to its starting row on the last frame and the loop
    closes seamlessly -- no visible seam where the GIF wraps.
    """
    rng = random.Random(seed)
    cols = []
    for _ in range(W):
        cols.append(
            {
                "speed": rng.choice((1, 1, 1, 2)),
                "phase": rng.randrange(CYCLE),
                "trail": rng.randint(5, 8),
            }
        )
    return cols


def flicker(x, y, t):
    """Deterministic per-pixel noise.

    Depends only on (x, y, t mod FRAMES), so the sparkle loops with everything
    else instead of popping at the wrap.
    """
    h = (x * 73856093) ^ (y * 19349663) ^ (t * 83492791)
    h = (h ^ (h >> 13)) & 0x7FFFFFFF
    return h % 100


def frame(cols, t):
    c = Canvas(PALETTE, W, H)
    for x, col in enumerate(cols):
        head = (col["phase"] + col["speed"] * t) % CYCLE
        for off in range(col["trail"] + 1):
            y = head - off
            if not (0 <= y < H):
                continue
            level = min(off, len(TRAIL) - 1)
            # A glyph changing character reads as a one-frame brightness jump;
            # keep it off the leader so the head stays the brightest pixel.
            if level > 0 and flicker(x, y, t) < 12:
                level = max(1, level - 2)
            c.put(x, y, TRAIL[level])
    return c


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    cols = columns()
    emit_animation(
        "matrix16", [frame(cols, t).pixels() for t in range(FRAMES)], here,
        delay_ms=DELAY_MS,
    )
    still = frame(cols, 0)
    still.emit("matrix16", here)
    print(still.ascii_art())
