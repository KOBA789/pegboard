import pytest
from build123d import Cylinder, GeomType, Pos

from hooks.switchbot_meter import meter as meter_module
from hooks.switchbot_meter import pocket
from pegboard import NPOLDA
from pegboard.export import fits_bed
from pegboard.shape import board_patch


@pytest.fixture(scope="module")
def part():
    return pocket.pocket()


@pytest.fixture(scope="module")
def meter():
    return pocket.meter_placement()


def test_single_valid_solid(part):
    assert part.is_valid
    assert len(part.solids()) == 1


def test_fits_bed_standing_on_its_floor(part):
    printed = pocket.printed(part)
    assert fits_bed(printed)
    # it stands on one flat face, the floor underside, nearly as large as the floor
    on_bed = [
        f
        for f in printed.faces()
        if f.geom_type == GeomType.PLANE and f.bounding_box().max.Z < 1e-4
    ]
    assert len(on_bed) == 1
    w_in, _ = pocket.widths()
    assert on_bed[0].area > w_in * meter_module.DEPTH


def test_seated_part_only_presses_into_the_peg_hole(part):
    board = board_patch(NPOLDA, range(-2, 3), range(-3, 2))
    overlap = part & board
    peg_hole = Pos(NPOLDA.hole(0, -pocket.P["peg_rows"])) * Cylinder(
        pocket.P["peg_d"] / 2 + 0.01, 20
    )
    assert (overlap - peg_hole).volume < 0.01
    assert (overlap & peg_hole).volume > 0.1


def test_board_side_is_flat_and_centred(part):
    back = [f for f in part.faces() if f.geom_type == GeomType.PLANE and abs(f.center().Z) < 1e-6]
    assert len(back) == 1
    bb = back[0].bounding_box()
    assert bb.min.X == pytest.approx(-bb.max.X, abs=0.01)


def test_meter_fits_the_pocket(part, meter):
    assert (meter & part).volume < 0.01
    # it stands on the floor: lowered by 0.1 mm it would cut into the pocket
    assert (Pos(0, -0.1, 0) * meter & part).volume > 0.1
    # and stands clear of the board
    assert meter.bounding_box().min.Z > 0.5


def test_meter_top_stays_open(part, meter):
    mb, pb = meter.bounding_box(), part.bounding_box()
    # nothing above the meter's top face (the vents), and it can be lifted out
    assert mb.max.Y > pb.max.Y + 10
    # the walls hold it in front and at the sides
    assert pb.max.Z > mb.max.Z
    assert pb.min.X < mb.min.X and pb.max.X > mb.max.X


def test_display_is_not_covered(part):
    assert (pocket.display_view() & part).volume < 0.01
    # but the lip and the ears do reach over the bezel up to near the display
    assert (pocket.display_view(grow=1.0) & part).volume > 0.1


def test_meter_is_snug(part):
    """clear_x a side all the way to the front (the cavity tapers like the meter), clear_z in
    front."""
    loc, _ = pocket.frame()
    meter = meter_module.model()
    cx, cz = pocket.P["clear_x"], pocket.P["clear_z"]
    for shift, gap in ((Pos(1, 0, 0), cx), (Pos(-1, 0, 0), cx), (Pos(0, 0, 1), cz)):
        near = loc * Pos(shift.position * (gap - 0.03)) * meter
        over = loc * Pos(shift.position * (gap + 0.03)) * meter
        assert (near & part).volume < 0.01
        assert (over & part).volume > 0.01
