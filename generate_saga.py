#!/usr/bin/env python3
"""16x16 two-minute saga: a skeleton raised into a samurai by purple magic.

Medieval Japan, at night, castle keeps on the ridge. Seven movements:

    0 - 15s   the keeps under a cold moon
   15 - 34s   a skeleton rises out of the ground
   34 - 60s   purple magic spirals in and tightens around it
   60 - 75s   the vortex closes, a white flash, and a samurai stands there
   75 - 97s   fire erupts across the ground
   97 - 112s  the keeps burning, the samurai before them
  112 - 120s  the fire dies and the night returns, closing the loop

960 frames at 125 ms, 120.00s exactly. The last frame lands on the first, so
it runs continuously.
"""

import math
import os

from pixelart import emit_animation, mix

W = H = 16
FRAMES = 1000
# GIF stores frame delays in hundredths of a second, so a delay has to be a
# multiple of 10 ms or the file quietly plays at a different speed than the
# exported arrays: 125 ms became 120 ms and cost the loop nearly five seconds.
DELAY_MS = 120
XFADE = 12          # frames of cross-dissolve between movements

GROUND = 13         # figures stand with their feet on this row
RIDGE = 12          # castles sit on the ridge behind

# --- palette ----------------------------------------------------------------
NIGHT_TOP = (0x06, 0x08, 0x22)
NIGHT_LOW = (0x24, 0x2E, 0x66)
STAR = (0xC8, 0xD8, 0xFF)
MOON = (0xF2, 0xEE, 0xD2)
KEEP = (0x07, 0x06, 0x12)       # castle silhouette
KEEP_LIT = (0x2A, 0x14, 0x30)   # castle edge, catching whatever light there is
EARTH = (0x0B, 0x09, 0x16)

BONE = (0xE6, 0xE2, 0xCC)
BONE_DARK = (0x8A, 0x86, 0x74)
SOCKET = (0x12, 0x08, 0x1A)

MAGIC = [
    (0x3A, 0x0C, 0x6E),   # deep violet, the far side of the orbit
    (0x6A, 0x18, 0xC0),
    (0x9A, 0x3C, 0xF0),
    (0xC8, 0x82, 0xFF),
    (0xEE, 0xD6, 0xFF),   # near-white, a mote passing in front
]

ARMOR = (0x1B, 0x12, 0x2C)
ARMOR_LIT = (0x3A, 0x2A, 0x52)
LACE = (0xB4, 0x1E, 0x34)       # the red lacing of the cuirass
GOLD = (0xE8, 0xB4, 0x38)       # kabuto crest
STEEL = (0xD8, 0xE4, 0xF0)

FIRE = [(0x6E, 0x0C, 0x04), (0xB8, 0x22, 0x06), (0xE8, 0x50, 0x0A),
        (0xFF, 0x8E, 0x14), (0xFF, 0xC8, 0x46), (0xFF, 0xEC, 0xA8)]

# --- sprites ----------------------------------------------------------------
SKELETON = [
    "..###..",
    ".#####.",
    ".#o#o#.",   # o marks an eye socket
    "..###..",
    "...#...",
    ".#####.",
    "##.#.##",
    ".#.#.#.",
    "..###..",
    "..#.#..",
    "..#.#..",
    "..#.#..",
]

SAMURAI = [
    "..g..g..",   # g: the gold crest of the kabuto
    "...gg...",
    "..aaaa..",
    ".aaaaaa.",
    "..affa..",   # f: the face under the helmet, in shadow
    ".alllla.",   # l: red lacing
    "aaaaaaaa",
    ".allula.",   # u: a lit plate catching the fire
    ".allala.",
    "..aaaa..",
    "..a..a..",
    "..a..a..",
]

# A tenshu: stacked tiers, each roof wider than the storey under it.
KEEP_SPRITE = [
    "....#....",
    "..#####..",
    "...###...",
    ".#######.",
    "..#####..",
    "#########",
    ".#######.",
    "#########",
]

# Narrower keep, for the movements where it shares the frame with the samurai:
# both are dark silhouettes, so they have to stand clear of each other.
KEEP_NARROW = [
    "...#...",
    ".#####.",
    "..###..",
    "#######",
    ".#####.",
    "#######",
    "..###..",
]
BURNING = [(9, KEEP_NARROW)]
HERO_X = 4          # samurai centre once the keeps move to the right

STARS = [(1, 1), (5, 2), (11, 1), (14, 3), (8, 0), (3, 4)]


def blank():
    return [[NIGHT_TOP for _ in range(W)] for _ in range(H)]


def sky(px, top, low, upto=GROUND):
    for y in range(upto):
        c = mix(top, low, y / max(1, upto - 1))
        for x in range(W):
            px[y][x] = c


def ground(px, colour=EARTH):
    for y in range(GROUND, H):
        for x in range(W):
            px[y][x] = colour


def noise(x, y, t):
    h = (x * 374761393) ^ (y * 668265263) ^ (t * 2246822519)
    return ((h ^ (h >> 15)) & 0x7FFFFFFF) % 100


RIDGE_KEEPS = [(1, KEEP_SPRITE), (10, KEEP_SPRITE[2:])]


def draw_keeps(px, placements=None, lit=0.0, glow=(0, 0, 0)):
    """Keeps on the ridge, as (left column, sprite) placements.

    The body stays a flat dark silhouette whatever is happening behind it --
    washing it with the firelight made it vanish into a red sky. Only the roof
    lines take the glow.
    """
    for x0, sprite in (placements or RIDGE_KEEPS):
        base = RIDGE - len(sprite) + 1
        for gy, row in enumerate(sprite):
            for gx, cell in enumerate(row):
                if cell != "#":
                    continue
                x, y = x0 + gx, base + gy
                if not (0 <= x < W and 0 <= y < H):
                    continue
                roofline = gy == 0 or sprite[gy - 1][gx] != "#"
                if roofline:
                    px[y][x] = mix(mix(KEEP, KEEP_LIT, 0.7), glow, lit)
                else:
                    px[y][x] = KEEP


def draw_figure(px, sprite, cx, base, palette, fade=1.0):
    """Sprite centred on cx with its feet on row `base`."""
    w = len(sprite[0])
    x0 = cx - w // 2
    for gy, row in enumerate(sprite):
        for gx, cell in enumerate(row):
            if cell == ".":
                continue
            x, y = x0 + gx, base - len(sprite) + 1 + gy
            if 0 <= x < W and 0 <= y < H:
                px[y][x] = mix(px[y][x], palette[cell], fade)


BONE_MAP = {"#": BONE, "o": SOCKET}
ARMOR_MAP = {"a": ARMOR, "l": LACE, "g": GOLD, "f": SOCKET, "u": ARMOR_LIT}


def draw_sword(px, cx, base, fade=1.0):
    """Katana held upright at the samurai's side, guard just below the grip."""
    for y in range(base - 9, base - 2):
        x = cx + 4
        if 0 <= x < W and 0 <= y < H:
            px[y][x] = mix(px[y][x], STEEL, fade)
    if 0 <= cx + 3 < W:
        px[base - 3][cx + 3] = mix(px[base - 3][cx + 3], GOLD, fade)


def swirl(px, t, tightness, intensity, in_front, cx=7.5, cy=8.0, count=14):
    """Purple motes orbiting the figure on a tilted ellipse.

    Half the orbit passes behind the figure, so the caller draws this twice --
    once before the figure and once after -- and the sign of sin(angle) says
    which pass a mote belongs to.
    """
    rx = 7.5 - 5.0 * tightness
    ry = rx * 0.42
    for k in range(count):
        ang = 2 * math.pi * k / count + t * 0.24 + k * 0.11
        front = math.sin(ang) > 0
        if front != in_front:
            continue
        x = cx + rx * math.cos(ang)
        y = cy + ry * math.sin(ang) - 1.5 * tightness
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < W and 0 <= yi < H):
            continue
        # Brighter in front, and brighter the tighter the orbit has become.
        level = 2 + (1 if front else 0) + int(2 * tightness)
        c = MAGIC[min(level, len(MAGIC) - 1)]
        px[yi][xi] = mix(px[yi][xi], c, intensity)
        # A short tail, one step back along the orbit.
        ang2 = ang - 0.30
        x2, y2 = cx + rx * math.cos(ang2), cy + ry * math.sin(ang2) - 1.5 * tightness
        xi2, yi2 = int(round(x2)), int(round(y2))
        if 0 <= xi2 < W and 0 <= yi2 < H and (xi2, yi2) != (xi, yi):
            px[yi2][xi2] = mix(px[yi2][xi2], MAGIC[max(0, level - 2)], intensity * 0.7)


def magic_glow(px, strength):
    """A purple wash rising off the ground while the spell gathers."""
    if strength <= 0:
        return
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - 7.5, (y - 9.0) * 1.4)
            f = max(0.0, 1.0 - d / 9.0) * strength
            if f > 0:
                px[y][x] = mix(px[y][x], MAGIC[1], f * 0.65)


def flames(px, t, height, cover=1.0):
    """Fire rising off the ground. `height` is rows above GROUND at full burn."""
    if height <= 0:
        return
    for x in range(W):
        col = height * (0.55 + 0.45 * math.sin(x * 1.7 + t * 0.5))
        col += (noise(x, 0, t) % 30) / 30.0 * 1.6 - 0.4
        top = GROUND - max(0, col)
        for y in range(H - 1, int(top) - 1, -1):
            if y < 0:
                continue
            frac = max(0.0, min(1.0, (GROUND - y) / max(0.8, col)))
            # Hottest at the base, cooling toward the tips -- but the base tops
            # out at orange, with only flecks going gold or white. Letting the
            # whole base run to the brightest colour turned it into a sand bar.
            level = int(round((1 - frac) * 3.2))
            n = noise(x, y, t)
            if n < 8:
                level += 2
            elif n < 26:
                level += 1
            level = max(0, min(len(FIRE) - 1, level))
            if y >= GROUND or noise(x, y, t + 7) > 18:
                px[y][x] = mix(px[y][x], FIRE[level], cover)
    # Embers, drifting up out of the fire.
    for k in range(4):
        ex = (k * 5 + (t // 2) % 16) % W
        ey = GROUND - 1 - ((t // 2 + k * 7) % (int(height) + 6))
        if 0 <= ey < H and height > 1:
            px[ey][ex] = mix(px[ey][ex], FIRE[4 + (k % 2)], cover * 0.9)


# --- movements --------------------------------------------------------------

def scene_night(u, t):
    px = blank()
    sky(px, NIGHT_TOP, NIGHT_LOW)
    for i, (x, y) in enumerate(STARS):
        # Eight twinkle cycles per loop exactly, so the stars carry across
        # the wrap instead of jumping when the animation restarts.
        tw = 0.5 + 0.5 * math.sin(2 * math.pi * 8 * t / FRAMES + i * 1.7)
        px[y][x] = mix(NIGHT_TOP, STAR, 0.35 + 0.65 * tw)
    # Moon, low and cold over the ridge.
    for y in range(H):
        for x in range(W):
            d = math.hypot(x + 0.5 - 12.5, y + 0.5 - 2.5)
            if d <= 1.9:
                px[y][x] = MOON if d < 1.2 else mix(NIGHT_LOW, MOON, 0.8)
            elif d <= 3.0:
                px[y][x] = mix(px[y][x], MOON, 0.10)
    draw_keeps(px)
    ground(px)
    return px


def scene_rise(u, t):
    px = scene_night(0, t)
    # The skeleton comes up out of the earth: its feet stay buried until it
    # has fully risen, so it emerges rather than slides into frame.
    lift = min(1.0, u * 1.6)
    base = GROUND + int(round((1 - lift) * 12))
    draw_figure(px, SKELETON, 7, base, BONE_MAP)
    ground(px)                      # earth redrawn over it: it rises through
    draw_figure(px, SKELETON, 7, base, BONE_MAP, fade=1.0 if base <= GROUND else 0)
    if u > 0.55:                    # sockets take a faint purple light
        glow = (u - 0.55) / 0.45
        for dx in (-1, 1):
            x, y = 7 + dx, GROUND - 9
            if 0 <= x < W:
                px[y][x] = mix(SOCKET, MAGIC[3], 0.5 * glow)
    return px


def scene_swirl(u, t):
    px = scene_night(0, t)
    magic_glow(px, u * 0.9)
    tight = u ** 0.8
    swirl(px, t, tight, 0.55 + 0.45 * u, in_front=False)
    draw_figure(px, SKELETON, 7, GROUND, BONE_MAP)
    for dx in (-1, 1):
        px[GROUND - 9][7 + dx] = mix(SOCKET, MAGIC[4], 0.5 + 0.5 * u)
    swirl(px, t, tight, 0.55 + 0.45 * u, in_front=True)
    return px


def scene_transform(u, t):
    px = scene_night(0, t)
    magic_glow(px, 0.9)
    tight = min(1.0, 1.0 + u * 0.0)          # already fully tightened
    # The flash: a bloom of white through the middle of the movement, which is
    # what covers the swap from bones to armour.
    flash = 0.92 * max(0.0, 1.0 - abs(u - 0.5) / 0.10)
    if u < 0.5:
        swirl(px, t, tight, 1.0, in_front=False)
        draw_figure(px, SKELETON, 7, GROUND, BONE_MAP)
        swirl(px, t, tight, 1.0, in_front=True)
    else:
        swirl(px, t, tight, 1.0 - (u - 0.5) * 1.2, in_front=False)
        draw_figure(px, SAMURAI, 7, GROUND, ARMOR_MAP)
        draw_sword(px, 7, GROUND)
        swirl(px, t, tight, 1.0 - (u - 0.5) * 1.2, in_front=True)
    if flash > 0:
        for y in range(H):
            for x in range(W):
                d = math.hypot(x - 7.5, y - 8.0)
                px[y][x] = mix(px[y][x], (0xFF, 0xF4, 0xFF),
                               flash * max(0.0, 1.0 - d / 11.0))
    return px


def scene_fire(u, t):
    px = blank()
    # Sky reddens as the fire takes hold.
    sky(px, mix(NIGHT_TOP, (0x2E, 0x06, 0x0A), u),
        mix(NIGHT_LOW, (0x9E, 0x22, 0x08), u))
    draw_keeps(px, BURNING, lit=u * 0.7, glow=(0x60, 0x18, 0x10))
    ground(px)
    height = 1 + 5 * min(1.0, u * 1.4)
    flames(px, t, height * 0.6, cover=0.85)      # fire behind the figure
    # He walks out of centre frame as the fire takes hold, which is what makes
    # room for the burning keep on the right without anything teleporting.
    cx = int(round(7 - (7 - HERO_X) * min(1.0, u * 2.5)))
    draw_figure(px, SAMURAI, cx, GROUND, ARMOR_MAP)
    draw_sword(px, cx, GROUND)
    flames(px, t, height, cover=0.55)            # and a veil of it in front
    return px


def scene_keeps(u, t):
    px = blank()
    sky(px, (0x2E, 0x06, 0x0A), (0xB0, 0x2C, 0x08))
    draw_keeps(px, BURNING, lit=0.75, glow=(0x80, 0x20, 0x10))
    # The keep alight, flames licking up over its roofs.
    for k in range(4):
        fx = 9 + k * 2
        fy = RIDGE - 6 - (noise(fx, k, t) % 3)
        if 0 <= fx < W and 0 <= fy < H:
            px[fy][fx] = mix(px[fy][fx], FIRE[3 + (k % 2)], 0.85)
    ground(px)
    flames(px, t, 5.5, cover=0.8)
    draw_figure(px, SAMURAI, HERO_X, GROUND, ARMOR_MAP)
    draw_sword(px, HERO_X, GROUND)
    flames(px, t, 3.0, cover=0.4)
    return px


def scene_return(u, t):
    """Fire dies, night comes back: this is what closes the loop."""
    night = scene_night(0, t)
    px = blank()
    sky(px, mix((0x2E, 0x06, 0x0A), NIGHT_TOP, u),
        mix((0xB0, 0x2C, 0x08), NIGHT_LOW, u))
    draw_keeps(px, BURNING, lit=0.75 * (1 - u), glow=(0x80, 0x20, 0x10))
    ground(px)
    flames(px, t, 5.5 * (1 - u) ** 1.5, cover=0.8 * (1 - u))
    draw_figure(px, SAMURAI, HERO_X, GROUND, ARMOR_MAP, fade=1.0 - u)
    draw_sword(px, HERO_X, GROUND, fade=1.0 - u)
    # Cross into the night frame itself over the back half, so the last frame
    # of the loop is the first frame of it.
    if u > 0.45:
        k = min(1.0, (u - 0.45) / 0.45)   # fully night before the last frame
        for y in range(H):
            for x in range(W):
                px[y][x] = mix(px[y][x], night[y][x], k)
    return px


MOVEMENTS = [
    (scene_night, 125),
    (scene_rise, 156),
    (scene_swirl, 219),
    (scene_transform, 125),
    (scene_fire, 187),
    (scene_keeps, 125),
    (scene_return, 63),
]

BOUNDS = []
_acc = 0
for _fn, _len in MOVEMENTS:
    BOUNDS.append((_fn, _acc, _acc + _len))
    _acc += _len
assert _acc == FRAMES, _acc


def render(i, t):
    fn, start, end = BOUNDS[i]
    return fn(min(1.0, max(0.0, (t - start) / (end - start))), t)


def frame(t):
    for i, (_fn, start, end) in enumerate(BOUNDS):
        if start <= t < end:
            px = render(i, t)
            if t >= end - XFADE and i + 1 < len(BOUNDS):
                k = (t - (end - XFADE)) / XFADE
                nxt = render(i + 1, t)
                px = [[mix(px[y][x], nxt[y][x], k) for x in range(W)]
                      for y in range(H)]
            return px
    raise ValueError(t)


def animate():
    return [frame(t) for t in range(FRAMES)]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    frames = animate()
    emit_animation("saga16", frames, here, delay_ms=DELAY_MS, scale=4)

    from PIL import Image
    im = Image.new("RGB", (W, H))
    im.putdata([frames[0][y][x] for y in range(H) for x in range(W)])
    im.save(os.path.join(here, "saga16.png"))
    im.resize((W * 32, H * 32), Image.NEAREST).save(
        os.path.join(here, "saga16_preview.png"))

    print("%d frames at %d ms = %.2fs"
          % (len(frames), DELAY_MS, len(frames) * DELAY_MS / 1000))
