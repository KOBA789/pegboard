"""ThinkPad TrackPoint Keyboard II, for fit checks."""

from build123d import Align, Axis, Box, Part, fillet

# Lenovo spec (ACC500164 product page)
LENGTH = 305.5
DEPTH = 164.0
HEIGHT = 13.7  # treated as the maximum thickness; not measured
WEIGHT_KG = 0.49
# The long edges are rounded; 2 mm is a conservative guess used only to check the fit.
EDGE_R = 2.0


def model(*, standing: bool = False) -> Part:
    """Box with rounded long edges and its min corner at the origin: x = length, then y = height
    and z = depth when lying flat, or y = depth and z = height when standing on its long edge."""
    size = (LENGTH, DEPTH, HEIGHT) if standing else (LENGTH, HEIGHT, DEPTH)
    box = Box(*size, align=Align.MIN)
    return fillet(box.edges().filter_by(Axis.X), EDGE_R)
