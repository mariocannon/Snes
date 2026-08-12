#!/usr/bin/env python3
"""16x16 TIE fighter silhouette that cycles through the spectrum.

The most literal palette animation in the set: the geometry never changes at
all. Every frame draws the same mask and only rotates the hue, so the ship
sweeps the colour wheel while its cockpit window stays cut out of it.

A TIE is the Star Wars shape that survives 16 px -- two slab wings and a ball,
all straight lines and hard corners. A helmet at this size just reads as a
face.
"""

import colorsys
import os

from pixelart import Canvas, emit_animation

W = H = 16
FRAMES = 32
DELAY_MS = 110

# '#' ship, '.' empty space. Hexagonal wing panels either side, the cockpit
# ball between them, and the struts running through on rows 7 and 8.
MASK = [
    "................",
    ".###........###.",
    "####........####",
    "####........####",
    "####........####",
    "####...##...####",
    "####..####..####",
    "################",
    "################",
    "####..####..####",
    "####...##...####",
    "####........####",
    "####........####",
    "####........####",
    ".###........###.",
    "................",
]

# The cockpit window, cut through to the dark.
WINDOW = [(7, 7), (8, 7), (7, 8), (8, 8)]

# A spar down each wing panel: without it the panels read as blank slabs.
SPARS = [(2, y) for y in range(3, 13)] + [(13, y) for y in range(3, 13)]

BASE = {
    ".": (0x05, 0x05, 0x09),  # space
    "k": (0x03, 0x03, 0x06),  # cockpit window
}


def hue_palette(t):
    """Hull, rim, spar and backglow at this frame's hue."""
    h = (t / FRAMES) % 1.0
    pal = dict(BASE)
    pal["H"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.85, 0.86))
    pal["h"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.45, 1.00))
    pal["d"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.95, 0.45))
    pal[":"] = tuple(int(v * 255) for v in colorsys.hsv_to_rgb(h, 0.90, 0.16))
    return pal


def build(palette):
    c = Canvas(palette, W, H)

    # A ring of backglow one pixel out from the silhouette, so the ship sits in
    # its own light instead of floating on flat black.
    for y in range(H):
        for x in range(W):
            if MASK[y][x] == "#":
                continue
            near = any(
                0 <= x + dx < W and 0 <= y + dy < H and MASK[y + dy][x + dx] == "#"
                for dx in (-1, 0, 1)
                for dy in (-1, 0, 1)
            )
            if near:
                c.put(x, y, ":")

    for y in range(H):
        for x in range(W):
            if MASK[y][x] == "#":
                c.put(x, y, "H")

    c.puts(SPARS, "d")

    # Rim light along the top edge only: the one thing giving a flat
    # single-colour shape any sense of form. Down the left side as well it
    # just put a heavy stripe through the silhouette.
    for x in range(W):
        for y in range(H):
            if MASK[y][x] == "#":
                c.put(x, y, "h")
                break

    c.puts(WINDOW, "k")
    return c


def animate():
    return [build(hue_palette(t)).pixels() for t in range(FRAMES)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    emit_animation("tie16", animate(), here, delay_ms=DELAY_MS)
    still = build(hue_palette(0))
    still.emit("tie16", here)
    print(still.ascii_art())
