"""The shared mount parts must reproduce the printed and tested HUB75 rails of the earlier
project (FreeCAD; not public). Reference values were taken by running that script with
FreeCAD 1.1.3 and are hard-coded below."""

import math

import pytest
from build123d import Box, Cylinder, Pos

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop, straight_length

# rail plate of the HUB75 rails, rebuilt in board coordinates (back face on z = 0)
L, H, T = 190.0, 19.0, 5.0
HOOK_X = (L / 2 - 75, L / 2 + 75)
ROD_Y = 14.0  # rod centre height on the top rail


def rail_plate():
    plate = Pos(L / 2, H / 2, T / 2) * Box(L, H, T)
    for i in (-1, 0, 1):
        x = L / 2 + i * 85
        plate -= Pos(x, 10, T / 2) * Cylinder(1.7, T)
        plate -= Pos(x, 10, 2.8 / 2) * Cylinder(3.25, 2.8)  # counterbore on the back face
    return plate


def test_straight_length():
    assert straight_length(NPOLDA, HookSpec()) == pytest.approx(2.3877223398316203)


def test_top_rail_matches_freecad():
    hole_y = ROD_Y + seat_drop(NPOLDA, 5.0)
    rail = rail_plate()
    for x in HOOK_X:
        rail += Pos(x, hole_y, 0) * bent_hook(NPOLDA)
    assert rail.is_valid
    assert rail.volume == pytest.approx(18199.541765670983, rel=1e-4)
    # depth = plate + straight run + bend + ball tip (FreeCAD's loose BoundBox said 17.23)
    depth = T + straight_length(NPOLDA, HookSpec()) + 8 * math.sin(math.radians(60)) + 2.5
    size = rail.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((190, 20.5, depth), abs=1e-3)


def test_bottom_rail_matches_freecad():
    peg_y = ROD_Y - (7 * 25 - 2 * 85) + seat_drop(NPOLDA, 5.0)
    rail = rail_plate()
    for x in HOOK_X:
        rail += Pos(x, peg_y, 0) * press_fit_peg(NPOLDA)
    assert rail.is_valid
    assert rail.volume == pytest.approx(17921.216914554374, rel=1e-4)


def test_flats_fit_the_hole():
    """A rod clipped to flats must still be inside the hole circle when seated."""
    hook = bent_hook(NPOLDA, flat_width=4.0)
    section = hook.faces().sort_by(lambda f: f.center().Z)[-1]  # embedded start face
    hr = NPOLDA.hole_d / 2
    for v in section.vertices():
        assert math.hypot(v.X, v.Y) <= hr
