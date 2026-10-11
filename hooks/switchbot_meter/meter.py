"""SwitchBot 温湿度計 (SwitchBot Meter), for fit checks."""

import math

from build123d import Align, Box, Part, Pos, Rectangle, extrude

# measured: 55 x 55 at the back, tapering to 54 x 54 at the front, 24 deep
WIDTH = 55.0  # x and y, back face
FRONT = 54.0  # x and y, front face
DEPTH = 24.0
BEZEL = 8.0  # measured, the frame round the display on the front face
# The real corners are rounded; the model keeps them sharp, which only makes the fit check
# stricter. The vents are on the top face, which the pocket leaves open.


def model() -> Part:
    """Back face on z = 0, centred in x, with the bottom edge of the back face on y = 0; the front
    is at z = DEPTH."""
    taper = math.degrees(math.atan((WIDTH - FRONT) / 2 / DEPTH))
    return extrude(Pos(0, WIDTH / 2, 0) * Rectangle(WIDTH, WIDTH), DEPTH, taper=taper)


def display_view(grow: float = 0.0) -> Part:
    """The prism in front of the display (the front face inside the bezel), grown by `grow` on
    every side, in the frame of model()."""
    w = FRONT - 2 * BEZEL + 2 * grow
    y0 = (WIDTH - FRONT) / 2 + BEZEL - grow  # the front face starts this far up (taper)
    return Pos(0, y0, DEPTH) * Box(w, w, 50, align=(Align.CENTER, Align.MIN, Align.MIN))
