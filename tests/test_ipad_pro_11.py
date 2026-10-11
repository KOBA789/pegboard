import pytest
from build123d import Align, Axis, Box, Cylinder, GeomType, Pos

from hooks.ipad_pro_11 import holder
from pegboard import NPOLDA
from pegboard.export import fits_bed, lay_on_side
from pegboard.shape import board_patch

P = holder.P

# name: (builder, peg rows below the hook, width)
PARTS = {
    "stop": (holder.stop, P["stop_peg_rows"], P["stop_width"]),
    "rail": (holder.rail, P["rail_peg_rows"], P["rail_width"]),
}


@pytest.fixture(scope="module", params=PARTS)
def variant(request):
    make, peg_rows, width = PARTS[request.param]
    return make(), peg_rows, width


@pytest.fixture(scope="module")
def placed():
    """Both parts on the board, and the iPad with its camera bump in place."""
    stop = holder.stop()
    rail = Pos(holder.rail_hole()) * holder.rail()
    pad, cam = holder.ipad_placement()
    return stop, rail, pad, cam


def hits(shape, parts) -> list[float]:
    return [(shape & part).volume for part in parts]


def test_single_valid_solid(variant):
    part, _, _ = variant
    assert part.is_valid
    assert len(part.solids()) == 1


def test_fits_bed_on_its_side(variant):
    part, _, width = variant
    printed = lay_on_side(part, face="-x")
    assert fits_bed(printed)
    assert printed.bounding_box().size.Z == pytest.approx(width, abs=0.1)


def test_seated_part_only_presses_into_the_peg_hole(variant):
    part, peg_rows, _ = variant
    board = board_patch(NPOLDA, range(-1, 2), range(-5, 2))
    overlap = part & board
    peg_hole = Pos(NPOLDA.hole(0, -peg_rows)) * Cylinder(P["peg_d"] / 2 + 0.01, 20)
    # the hook rod rests on the bottom of its hole: tangent contact only
    assert (overlap - peg_hole).volume < 0.01
    # the press-fit peg is slightly larger than its hole
    assert (overlap & peg_hole).volume > 0.1


def test_board_side_is_flat_and_centred(variant):
    part, _, width = variant
    back = [f for f in part.faces() if f.geom_type == GeomType.PLANE and abs(f.center().Z) < 1e-6]
    assert len(back) == 1
    bb = back[0].bounding_box()
    assert bb.size.X == pytest.approx(width, abs=0.01)
    assert bb.min.X == pytest.approx(-bb.max.X, abs=0.01)


def test_ipad_fits(placed):
    stop, rail, pad, cam = placed
    assert max(hits(pad, [stop, rail])) < 0.01
    assert max(hits(cam, [stop, rail])) < 0.01
    # the camera bump stays clear of the board
    assert cam.bounding_box().min.Z > 1.0


def test_ipad_is_seated(placed):
    """It stands on both floors, leans on both plates and touches the stop."""
    stop, rail, pad, _ = placed
    assert min(hits(Pos(0, -0.1, 0) * pad, [stop, rail])) > 0.1
    assert min(hits(Pos(0, 0, -0.1) * pad, [stop, rail])) > 0.1
    assert hits(Pos(-0.1, 0, 0) * pad, [stop])[0] > 0.1


def test_ipad_cannot_tip_or_kick_out(placed):
    stop, rail, pad, _ = placed
    bb = pad.bounding_box()
    # pulled straight forward, both bottom lips and the left lip hold it
    assert min(hits(Pos(0, 0, 1.0) * pad, [stop, rail])) > 0.1
    # top tipping forward about the bottom edge: the left lip holds it
    bottom_back = Axis((0, bb.min.Y, bb.min.Z), (1, 0, 0))
    assert hits(pad.rotate(bottom_back, 1.0), [stop])[0] > 0.1
    # right end swinging forward about the left edge: the rail's lip holds it
    left_back = Axis((bb.min.X, 0, bb.min.Z), (0, 1, 0))
    assert hits(pad.rotate(left_back, -1.0), [rail])[0] > 0.1


@pytest.mark.parametrize("dx", [0.5, 10, 50, 150, 250, 300])
def test_ipad_slides_out_to_the_right(placed, dx):
    stop, rail, pad, cam = placed
    assert max(hits(Pos(dx, 0, 0) * pad, [stop, rail])) < 0.01
    assert max(hits(Pos(dx, 0, 0) * cam, [stop, rail])) < 0.01


def test_top_and_right_edges_are_free(placed):
    """Nothing near the top edge (Apple Pencil) or the right edge (USB-C)."""
    stop, rail, pad, _ = placed
    bb = pad.bounding_box()
    above = Pos(bb.min.X, bb.max.Y - 20, -50) * Box(1000, 1000, 1000, align=Align.MIN)
    right = Pos(bb.max.X - 20, -500, -50) * Box(1000, 1000, 1000, align=Align.MIN)
    for part in (stop, rail):
        assert (part & above).volume < 0.01
        assert (part & right).volume < 0.01
