#!/usr/bin/env python3
"""16x16 Japanese garden stone lantern at night.

An ishidoro standing in a garden: hoju finial, curved kasa roof with its eaves
turned up at the corners, the hibukuro firebox glowing between them, then the
platform, post and base, with moss at the foot and grass either side.

Unlike the paper lantern, the light here escapes only through the firebox
windows -- so the piece is lit rather than coloured. Everything is drawn in
its own stone or earth colour first, then a lighting pass warms each pixel by
how close it is to the firebox, which is what makes a heavy grey object read
as being lit from inside.

80 frames at 100 ms (8.0 s).
"""

import math
import os

from pixelart import emit_animation, mix

W = H = 16
FRAMES = 80
DELAY_MS = 100

NIGHT_TOP = (0x04, 0x07, 0x0E)
NIGHT_LOW = (0x08, 0x0D, 0x14)
STONE = (0x56, 0x5A, 0x52)
STONE_DARK = (0x2C, 0x30, 0x2C)
MOSS = (0x27, 0x3C, 0x1E)
GRASS = (0x16, 0x24, 0x14)
EARTH = (0x14, 0x14, 0x12)
WINDOW_DIM = (0x8E, 0x4A, 0x10)
WINDOW_HOT = (0xFF, 0xC0, 0x52)
WARM = (0xFF, 0x9E, 0x38)      # the colour the light lays over everything else

# S stone, D stone in shadow, W firebox window, M moss, g grass, e earth
TORO = [
    ".......SS.......",   # hoju, the finial
    ".....SSSSSS.....",
    ".S.SSSSSSSSSS.S.",   # eaves turned up at the corners
    "..SSSSSSSSSSSS..",
    "....DDDDDDDD....",   # the roof's underside, in its own shadow
    ".....SSWWSS.....",   # hibukuro, with a round moon window cut through it
    ".....SWWWWS.....",
    ".....SWWWWS.....",
    ".....SSWWSS.....",
    "....SSSSSSSS....",   # chudai, the platform under the firebox
    ".......SS.......",   # sao, the post
    ".......SS.......",
    ".....SSSSSS.....",
    "...MSSSSSSSSM...",   # base, mossed where it meets the ground
    "eeeeeeeeeeeeeeee",
    "gg.eeeeeeeeee.gg",
]

FIRE_X, FIRE_Y = 7.5, 6.5

GUST = (52, 0.16, 9)     # one slow sag in the flame, per loop


def flame(t):
    """Calmer than a paper lantern's candle: stone hoods most of the draught."""
    ph = 2 * math.pi * t / FRAMES
    v = (0.74
         + 0.10 * math.sin(4 * ph)
         + 0.06 * math.sin(9 * ph + 1.1)
         + 0.035 * math.sin(17 * ph + 2.2))
    centre, depth, width = GUST
    d = abs(t - centre)
    d = min(d, FRAMES - d)
    if d < width:
        v -= depth * (1 - d / width) ** 2
    return max(0.35, min(1.0, v))


def frame(t):
    lvl = flame(t)
    fx = FIRE_X + 0.30 * math.sin(2 * math.pi * 6 * t / FRAMES + 0.7)

    px = [[NIGHT_TOP for _ in range(W)] for _ in range(H)]
    for y in range(H):
        for x in range(W):
            px[y][x] = mix(NIGHT_TOP, NIGHT_LOW, y / (H - 1))

    base = {"S": STONE, "D": STONE_DARK, "M": MOSS, "g": GRASS, "e": EARTH}
    kind = [[TORO[y][x] for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            c = kind[y][x]
            if c in base:
                px[y][x] = base[c]

    # --- lighting ----------------------------------------------------------
    for y in range(H):
        for x in range(W):
            if kind[y][x] == "W":
                continue
            d = math.hypot((x + 0.5 - fx) * 0.85, (y + 0.5 - FIRE_Y) * 0.95)
            k = max(0.0, 1.0 - d / 9.0) ** 2.1 * lvl
            # Surfaces below the firebox catch more: the roof caps the light,
            # so it falls on the platform, the post and the ground, not the sky.
            if y > FIRE_Y:
                k *= 1.35
            elif y < 5:
                k *= 0.35
            px[y][x] = mix(px[y][x], WARM, min(0.85, k))

    for y in range(H):
        for x in range(W):
            if kind[y][x] == "W":
                px[y][x] = mix(WINDOW_DIM, WINDOW_HOT, lvl)

    return px


def animate():
    return [frame(t) for t in range(FRAMES)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    frames = animate()
    emit_animation("toro16", frames, here, delay_ms=DELAY_MS)

    from PIL import Image
    im = Image.new("RGB", (W, H))
    im.putdata([frames[0][y][x] for y in range(H) for x in range(W)])
    im.save(os.path.join(here, "toro16.png"))
    im.resize((W * 32, H * 32), Image.NEAREST).save(
        os.path.join(here, "toro16_preview.png"))

    print("%d frames at %d ms = %.2fs   flame %.2f - %.2f"
          % (len(frames), DELAY_MS, len(frames) * DELAY_MS / 1000,
             min(flame(t) for t in range(FRAMES)),
             max(flame(t) for t in range(FRAMES))))
