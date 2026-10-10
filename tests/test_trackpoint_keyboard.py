import pytest
from build123d import Cylinder, GeomType, Pos
from conftest import load_hook

from pegboard.export import fits_bed, lay_on_side

kb = load_hook("trackpoint_keyboard")


@pytest.fixture(scope="module")
def cradle():
    return kb.cradle()


@pytest.fixture(scope="module")
def board():
    return kb.board_patch()


def test_single_valid_solid(cradle):
    assert cradle.is_valid
    assert len(cradle.solids()) == 1


def test_fits_bed_on_its_side(cradle):
    printed = lay_on_side(cradle, face="-x")
    assert fits_bed(printed)
    assert printed.bounding_box().size.Z == pytest.approx(kb.P["width"])


def test_seated_cradle_only_presses_into_the_peg_hole(cradle, board):
    overlap = cradle & board
    peg_hole = Pos(kb.NPOLDA.hole(0, -kb.P["peg_rows"])) * Cylinder(kb.P["peg_d"] / 2 + 0.01, 20)
    # the hook rod rests on the bottom of its hole: tangent contact only
    assert (overlap - peg_hole).volume < 0.01
    # the press-fit peg is slightly larger than its hole
    assert (overlap & peg_hole).volume > 0.1


def test_board_side_is_flat(cradle):
    """The face against the board must not be rounded off at its edges (that leaves a gap)."""
    back = [f for f in cradle.faces() if f.geom_type == GeomType.PLANE and abs(f.center().Z) < 1e-6]
    assert len(back) == 1
    bb = back[0].bounding_box()
    assert bb.size.X == pytest.approx(kb.P["width"], abs=0.01)


def test_hook_and_peg_reach_behind_the_board(cradle):
    bb = cradle.bounding_box()
    assert bb.min.Z < -kb.NPOLDA.thickness


def test_keyboard_fits_the_channel(cradle, board):
    keyboard, top_back_z = kb.keyboard_placement()
    assert (keyboard & cradle).volume < 0.01
    assert (keyboard & board).volume < 0.01
    assert top_back_z > 0.5  # the leaning keyboard must not touch the board at the top
