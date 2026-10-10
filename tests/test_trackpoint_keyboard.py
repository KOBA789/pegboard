import pytest
from build123d import Cylinder, GeomType, Pos

from hooks.trackpoint_keyboard import cradle, shelf
from pegboard import NPOLDA
from pegboard.export import fits_bed, lay_on_side
from pegboard.shape import board_patch

# (module, part builder, laid diagonally on the bed)
VARIANTS = {
    "cradle": (cradle, cradle.cradle, False),
    "shelf": (shelf, shelf.bracket, True),
}


@pytest.fixture(scope="module", params=VARIANTS)
def variant(request):
    module, make, diagonal = VARIANTS[request.param]
    return module, make(), diagonal


@pytest.fixture(scope="module")
def board():
    return board_patch(NPOLDA, range(-1, 2), range(-4, 2))


def test_single_valid_solid(variant):
    _, part, _ = variant
    assert part.is_valid
    assert len(part.solids()) == 1


def test_fits_bed_on_its_side(variant):
    module, part, diagonal = variant
    printed = lay_on_side(part, face="-x", diagonal=diagonal)
    assert fits_bed(printed)
    # the bounding box of the B-spline corner blends from soft_extrude can be ~0.1 mm loose
    assert printed.bounding_box().size.Z == pytest.approx(module.P["width"], abs=0.1)


def test_seated_part_only_presses_into_the_peg_hole(variant, board):
    module, part, _ = variant
    overlap = part & board
    peg_hole = Pos(NPOLDA.hole(0, -module.P["peg_rows"])) * Cylinder(
        module.P["peg_d"] / 2 + 0.01, 20
    )
    # the hook rod rests on the bottom of its hole: tangent contact only
    assert (overlap - peg_hole).volume < 0.01
    # the press-fit peg is slightly larger than its hole
    assert (overlap & peg_hole).volume > 0.1


def test_board_side_is_flat(variant):
    """The face against the board must not be rounded off at its edges (that leaves a gap)."""
    module, part, _ = variant
    back = [f for f in part.faces() if f.geom_type == GeomType.PLANE and abs(f.center().Z) < 1e-6]
    assert len(back) == 1
    bb = back[0].bounding_box()
    assert bb.size.X == pytest.approx(module.P["width"], abs=0.01)
    # it bears on both sides of the hook / peg column (x = 0), so the part cannot twist sideways
    assert bb.min.X == pytest.approx(-bb.max.X, abs=0.01)


def test_keyboard_fits_the_cradle():
    part = cradle.cradle()
    keyboard, top_back_z = cradle.keyboard_placement()
    assert (keyboard & part).volume < 0.01
    assert top_back_z > 0.5  # the leaning keyboard must not touch the board at the top


def test_keyboard_fits_the_shelf():
    part = shelf.bracket()
    keyboard = shelf.keyboard_placement()
    assert (keyboard & part).volume < 0.01
    # it rests on the shelf: lowered by 0.1 mm it would cut into the bracket
    assert (Pos(0, -0.1, 0) * keyboard & part).volume > 0.1
    # and the lip is in front of it
    assert part.bounding_box().max.Z > keyboard.bounding_box().max.Z
