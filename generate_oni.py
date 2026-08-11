#!/usr/bin/env python3
"""16x16 cyberpunk oni mask for an LED matrix.

A red oni glaring out of the dark: bone horns, heavy brows, blown-out cyan
eyes, and a tusked grin. Magenta and cyan rim lights trace the jaw so the
silhouette survives against a near-black background.
"""

import os

from pixelart import Canvas

PALETTE = {
    ".": (0x08, 0x05, 0x16),  # background
    ":": (0x2B, 0x0A, 0x3E),  # halo glow behind the mask
    "R": (0xC8, 0x10, 0x2E),  # face, base red
    "r": (0xFF, 0x45, 0x3A),  # face, lit red
    "d": (0x74, 0x08, 0x22),  # face, shadow
    "H": (0xF2, 0xE3, 0xC6),  # horn, bone
    "h": (0xA8, 0x8A, 0x62),  # horn, shadow side
    "k": (0x11, 0x02, 0x0B),  # brow / mouth interior
    "f": (0xDE, 0xC5, 0x9A),  # tooth row, bone
    "F": (0xFF, 0xF4, 0xE0),  # tusks, hot white
    "e": (0x00, 0xE5, 0xFF),  # eye, cyan
    "E": (0xDF, 0xFC, 0xFF),  # eye, hot core
    "n": (0xFF, 0x4D, 0x6D),  # tongue
    "p": (0xFF, 0x2F, 0xD0),  # magenta rim light (left)
    "q": (0x2B, 0xB8, 0xFF),  # cyan rim light (right)
}


def build():
    c = Canvas(PALETTE)

    # --- halo --------------------------------------------------------------
    # A soft ring behind the head; the mask is drawn over most of it, leaving
    # just enough glow at the edges to lift the silhouette off the black.
    c.disc(8, 8, 7.2, ":")

    # The mask is symmetric, so only the left half (x <= 7) is drawn and then
    # mirrored; the rim lights afterwards are the one asymmetric element.

    # --- horn --------------------------------------------------------------
    # A two-pixel-thick diagonal sweeping up and out, drawn before the face so
    # the skull overlaps its base.
    c.puts([(1, 0), (2, 0), (2, 1), (3, 1)], "H")
    c.puts([(1, 1), (3, 2)], "h")

    # --- head --------------------------------------------------------------
    # Widest at the brow, tapering to a heavy jaw.
    c.rect(4, 2, 7, 2, "R")
    c.rect(3, 3, 7, 3, "R")
    c.rect(2, 4, 7, 11, "R")
    c.rect(3, 12, 7, 12, "R")
    c.rect(5, 13, 7, 13, "R")
    c.rect(6, 14, 7, 14, "d")
    # Forehead catch-light and cheek shading give the flat red some volume.
    c.rect(5, 3, 7, 3, "r")
    c.rect(6, 4, 7, 4, "r")
    c.puts([(2, 11), (3, 12), (4, 12)], "d")

    # --- brow and eye ------------------------------------------------------
    # The brow drops from a high outer end toward the nose; the whole scowl
    # lives in these few pixels, so it gets the full 2-row stair.
    c.puts([(2, 5), (3, 5), (4, 6), (5, 6), (6, 6)], "k")
    c.rect(3, 7, 5, 7, "e")
    c.put(4, 7, "E")

    # --- nose and mouth ----------------------------------------------------
    c.put(7, 9, "k")            # nostril
    c.rect(4, 10, 7, 10, "f")   # upper tooth row
    c.put(4, 11, "F")           # tusk curling down past the lip
    c.rect(5, 11, 7, 11, "k")   # mouth interior
    c.rect(6, 12, 7, 12, "k")
    c.put(7, 12, "n")           # tongue

    c.mirror_x()

    # --- rim lights --------------------------------------------------------
    # Magenta from the left, cyan from the right: the neon-street lighting
    # that ties this piece to the torii scene, and the only thing separating
    # the jaw from the background at low panel brightness.
    c.puts([(2, 7), (2, 8), (2, 9), (2, 10), (3, 11), (4, 12)], "p")
    c.puts([(13, 7), (13, 8), (13, 9), (13, 10), (12, 11), (11, 12)], "q")

    return c


if __name__ == "__main__":
    canvas = build()
    canvas.emit("oni16", os.path.dirname(os.path.abspath(__file__)))
    print(canvas.ascii_art())
