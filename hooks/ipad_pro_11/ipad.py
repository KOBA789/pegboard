"""iPad Pro 11-inch (3rd generation, M1, 2021), for fit checks.

Held in landscape with the USB-C port on the right: Apple Pencil (2nd generation) then charges on
the top edge, the front camera is in the left border and the rear camera is at the top left of the
back (seen from the front).
"""

from build123d import Align, Box, Part, Pos, fillet

# Apple spec (nominal)
WIDTH = 247.6  # long side, along x
HEIGHT = 178.5  # short side, along y
THICKNESS = 5.9
WEIGHT_KG = 0.466  # Wi-Fi model; Apple Pencil (2nd generation) adds 0.021
# Estimated, not measured:
BEZEL = 8.9  # display border, from the 2388 x 1668 px display at 264 ppi (229.8 x 160.5 mm)
CAMERA_BUMP = 1.5  # rear camera module, sticking out of the back
CAMERA_SIZE = 31.0  # square module ...
CAMERA_INSET = 8.0  # ... this far in from the left and top edges (seen from the front)
# The flat sides meet the faces in small rounds; 0.5 mm is smaller than the real ones and is used
# only so the box does not catch on the channel's inner corner fillets.
EDGE_R = 0.5


def model() -> Part:
    """Landscape, min corner at the origin: x = width (USB-C at x = WIDTH, Pencil on y = HEIGHT),
    y = height, z = thickness with the back on z = 0 and the display on z = THICKNESS."""
    return fillet(Box(WIDTH, HEIGHT, THICKNESS, align=Align.MIN).edges(), EDGE_R)


def camera() -> Part:
    """The rear camera bump behind the back face (z < 0), in the frame of model()."""
    s = CAMERA_SIZE
    corner = (CAMERA_INSET, HEIGHT - CAMERA_INSET - s, -CAMERA_BUMP)
    return Pos(*corner) * Box(s, s, CAMERA_BUMP, align=Align.MIN)
