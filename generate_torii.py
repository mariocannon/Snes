#!/usr/bin/env python3
"""16x16 Japanese-cyberpunk torii scene for an LED matrix.

A neon torii gate silhouetted against a rising red sun, framed by a dark
skyline with cyan windows and a wet neon-lit street.
"""

import os

from pixelart import Canvas

# Kept small and high-contrast: LED panels crush subtle tones, and adjacent
# hues need to stay separable at 1px.
PALETTE = {
    ".": (0x0A, 0x06, 0x1E),  # night sky
    ":": (0x25, 0x0E, 0x4A),  # sky glow around the sun
    "s": (0x9F, 0xC8, 0xFF),  # star
    "1": (0xB3, 0x0F, 0x2A),  # sun, outer rim
    "2": (0xFF, 0x3B, 0x1F),  # sun, body
    "3": (0xFF, 0xA5, 0x3A),  # sun, core
    "T": (0xFF, 0x2F, 0xD0),  # torii, neon magenta
    "t": (0xFF, 0x9C, 0xEB),  # torii, lit edge
    "B": (0x1C, 0x12, 0x46),  # building silhouette
    "b": (0x2E, 0x20, 0x66),  # building, lit face
    "w": (0x00, 0xE5, 0xFF),  # window, cyan
    "W": (0xB6, 0xFB, 0xFF),  # window, hot
    "g": (0x0B, 0x06, 0x1C),  # street
    "G": (0x15, 0x0C, 0x32),  # wet asphalt sheen
    "m": (0x8A, 0x18, 0x70),  # torii reflection on wet asphalt
    "c": (0x0A, 0x6E, 0x8A),  # cyan reflection on wet asphalt
}


def build():
    c = Canvas(PALETTE)

    # --- sky + sun ---------------------------------------------------------
    c.disc(8, 6, 5.6, ":")
    c.disc(8, 6, 4.0, "1")
    c.disc(8, 6, 3.0, "2")
    c.disc(8, 6, 1.8, "3")
    c.puts([(0, 0), (6, 0), (13, 0)], "s")

    # --- skyline -----------------------------------------------------------
    # Staggered rooflines so the block reads as a city rather than a wall; the
    # two tall towers frame the gate.
    c.rect(0, 10, 0, 13, "B")
    c.rect(1, 8, 1, 13, "b")
    c.rect(2, 11, 2, 13, "B")
    c.rect(13, 11, 13, 13, "B")
    c.rect(14, 8, 14, 13, "b")
    c.rect(15, 10, 15, 13, "B")
    c.put(1, 7, "w")   # antenna beacons on the towers
    c.put(14, 7, "W")
    # Low buildings between the pillars, roofs kept under the sun's lower edge.
    c.rect(5, 12, 7, 13, "B")
    c.rect(8, 11, 10, 13, "b")

    c.puts([(1, 9), (1, 12), (2, 12), (14, 9), (14, 12), (13, 13), (9, 12), (6, 13)], "w")
    c.puts([(14, 10), (1, 11)], "W")
    # Vertical neon signboard hanging off the right-hand block.
    for y, ch in ((10, "t"), (11, "T"), (12, "t")):
        c.put(15, y, ch)

    # --- torii -------------------------------------------------------------
    c.rect(1, 1, 14, 1, "t")    # kasagi, lit top edge, overhanging both pillars
    c.rect(2, 2, 13, 2, "T")    # kasagi body
    c.rect(2, 5, 13, 5, "T")    # nuki (second beam), overhanging the pillars
    c.rect(3, 3, 3, 13, "T")    # left pillar
    c.rect(12, 3, 12, 13, "T")  # right pillar
    c.puts([(3, 5), (12, 5)], "t")  # lit joints where the beam crosses the pillars

    # --- street ------------------------------------------------------------
    c.rect(0, 14, 15, 14, "g")
    c.rect(0, 15, 15, 15, "G")
    for x in (3, 12):
        c.put(x, 14, "m")
        c.put(x, 15, "m")
    c.puts([(1, 15), (14, 15), (6, 15), (9, 15)], "c")

    return c


if __name__ == "__main__":
    canvas = build()
    canvas.emit("torii16", os.path.dirname(os.path.abspath(__file__)))
    print(canvas.ascii_art())
