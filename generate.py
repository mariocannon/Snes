#!/usr/bin/env python3
"""Generate a 16x16 Japanese-cyberpunk pixel scene for an LED matrix.

Scene: a neon torii gate silhouetted against a rising red sun, framed by a
dark skyline with cyan windows and a wet neon-lit street.

Outputs (written next to this script):
  torii16.png          - the real 16x16 image, ready for the panel
  torii16_preview.png  - 32x nearest-neighbour blow-up with a pixel grid
  torii16.json         - row-major RGB + hex data
  torii16.h            - C header: RGB888 and RGB565 arrays
"""

import json
import os

from PIL import Image, ImageDraw

W = H = 16

# --- palette ---------------------------------------------------------------
# Kept small and high-contrast: LED panels crush subtle tones, and adjacent
# hues need to stay separable at 1px.
P = {
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

grid = [["." for _ in range(W)] for _ in range(H)]


def put(x, y, ch):
    if 0 <= x < W and 0 <= y < H:
        grid[y][x] = ch


def disc(cx, cy, r, ch):
    """Filled circle in cell-center coordinates."""
    for y in range(H):
        for x in range(W):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                put(x, y, ch)


def rect(x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, ch)


# --- sky + sun -------------------------------------------------------------
disc(8, 6, 5.6, ":")
disc(8, 6, 4.0, "1")
disc(8, 6, 3.0, "2")
disc(8, 6, 1.8, "3")

for x, y in [(0, 0), (6, 0), (13, 0)]:
    put(x, y, "s")

# --- skyline ---------------------------------------------------------------
# Staggered rooflines so the block reads as a city rather than a wall; the
# two tall towers frame the gate.
rect(0, 10, 0, 13, "B")
rect(1, 8, 1, 13, "b")
rect(2, 11, 2, 13, "B")
rect(13, 11, 13, 13, "B")
rect(14, 8, 14, 13, "b")
rect(15, 10, 15, 13, "B")
put(1, 7, "w")   # antenna beacons on the towers
put(14, 7, "W")
# Low buildings between the pillars, roofs kept under the sun's lower edge.
rect(5, 12, 7, 13, "B")
rect(8, 11, 10, 13, "b")

for x, y in [(1, 9), (1, 12), (2, 12), (14, 9), (14, 12), (13, 13), (9, 12), (6, 13)]:
    put(x, y, "w")
for x, y in [(14, 10), (1, 11)]:
    put(x, y, "W")
# Vertical neon signboard hanging off the right-hand block.
for y, ch in ((10, "t"), (11, "T"), (12, "t")):
    put(15, y, ch)

# --- torii -----------------------------------------------------------------
rect(1, 1, 14, 1, "t")    # kasagi, lit top edge, overhanging both pillars
rect(2, 2, 13, 2, "T")    # kasagi body
rect(2, 5, 13, 5, "T")    # nuki (second beam), overhanging the pillars
rect(3, 3, 3, 13, "T")    # left pillar
rect(12, 3, 12, 13, "T")  # right pillar
for x, y in [(3, 5), (12, 5)]:
    put(x, y, "t")        # lit joints where the beam crosses the pillars

# --- street ----------------------------------------------------------------
rect(0, 14, 15, 14, "g")
rect(0, 15, 15, 15, "G")
for x in [3, 12]:
    put(x, 14, "m")
    put(x, 15, "m")
for x, y in [(1, 15), (14, 15), (6, 15), (9, 15)]:
    put(x, y, "c")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pixels = [[P[grid[y][x]] for x in range(W)] for y in range(H)]

    img = Image.new("RGB", (W, H))
    img.putdata([pixels[y][x] for y in range(H) for x in range(W)])
    img.save(os.path.join(here, "torii16.png"))

    # Preview: 32x blow-up with a faint grid so single pixels stay countable.
    scale = 32
    big = img.resize((W * scale, H * scale), Image.NEAREST).convert("RGB")
    d = ImageDraw.Draw(big)
    for i in range(1, W):
        d.line([(i * scale, 0), (i * scale, H * scale)], fill=(60, 60, 70))
        d.line([(0, i * scale), (W * scale, i * scale)], fill=(60, 60, 70))
    big.save(os.path.join(here, "torii16_preview.png"))

    hex_rows = ["".join("%02X%02X%02X" % p for p in row) for row in pixels]
    with open(os.path.join(here, "torii16.json"), "w") as f:
        json.dump(
            {
                "width": W,
                "height": H,
                "order": "row-major, top-left origin",
                "rows_hex": hex_rows,
                "pixels_rgb": pixels,
            },
            f,
            indent=2,
        )

    def rgb565(p):
        r, g, b = p
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    lines = [
        "// 16x16 Japanese-cyberpunk torii scene. Row-major, top-left origin.",
        "// Generated by generate.py -- edit the grid there, not here.",
        "#pragma once",
        "#include <stdint.h>",
        "",
        "#define TORII16_W 16",
        "#define TORII16_H 16",
        "",
        "static const uint32_t torii16_rgb888[256] = {",
    ]
    for row in pixels:
        lines.append(
            "    " + " ".join("0x%02X%02X%02X," % p for p in row)
        )
    lines += ["};", "", "static const uint16_t torii16_rgb565[256] = {"]
    for row in pixels:
        lines.append("    " + " ".join("0x%04X," % rgb565(p) for p in row))
    lines += ["};", ""]
    with open(os.path.join(here, "torii16.h"), "w") as f:
        f.write("\n".join(lines))

    for row in grid:
        print("".join(row))


if __name__ == "__main__":
    main()
