#!/usr/bin/env python3
"""16x16 panel calibration pattern.

Display this and the panel tells you how it is wired. Every element is
asymmetric on purpose, so no rotation, flip or wiring order produces the same
picture as any other:

  corners   white top-left, red top-right, green bottom-left, blue bottom-right
  arrow     yellow, pointing up, offset left of centre
  diagonal  magenta, running top-left to bottom-right

Read it like this:

  * White block is not top-left  -> the origin is that corner. Rotate or flip
    until it lands top-left; the corner colours say which.
  * Arrow points down / sideways -> rotation. Arrow mirrored but corners right
    -> a flip, not a rotation.
  * Diagonal is a zigzag or the rows look shuffled -> serpentine wiring. Every
    odd row is being drawn backwards.
  * Only part of the pattern fills the panel -> the image is being scaled or
    cropped by whatever is loading it, not by the file.

Then run panelfit.py with the matching options to re-emit any piece.
"""

import os

from pixelart import Canvas

PALETTE = {
    ".": (0x08, 0x08, 0x0C),  # background
    "W": (0xFF, 0xFF, 0xFF),  # top-left corner: the origin
    "R": (0xFF, 0x20, 0x20),  # top-right
    "G": (0x20, 0xE0, 0x30),  # bottom-left
    "B": (0x30, 0x60, 0xFF),  # bottom-right
    "Y": (0xFF, 0xD0, 0x20),  # up arrow
    "M": (0xFF, 0x30, 0xC0),  # diagonal
}


def build():
    c = Canvas(PALETTE)

    # Diagonal first, so the corner blocks and arrow sit on top of it.
    for i in range(16):
        c.put(i, i, "M")

    # Up arrow, deliberately off-centre to the left so a horizontal flip is
    # obvious even when the arrow itself still points up.
    c.puts([(6, 5), (5, 6), (6, 6), (7, 6), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)], "Y")
    c.rect(5, 8, 7, 11, "Y")

    # Corner blocks last: these are the primary read.
    c.rect(0, 0, 1, 1, "W")
    c.rect(14, 0, 15, 1, "R")
    c.rect(0, 14, 1, 15, "G")
    c.rect(14, 14, 15, 15, "B")
    return c


if __name__ == "__main__":
    canvas = build()
    canvas.emit("probe16", os.path.dirname(os.path.abspath(__file__)))
    print(canvas.ascii_art())
