import pytest
from build123d import Cylinder, Pos

from hooks.plate import build
from pegboard import NPOLDA
from pegboard.export import fits_bed, on_bed
from pegboard.shape import board_patch


@pytest.fixture(scope="module")
def part():
    return build.plate()


def test_single_valid_solid(part):
    assert part.is_valid
    assert len(part.solids()) == 1


def test_size(part):
    bb = part.bounding_box()
    assert (bb.min.X, bb.max.X) == pytest.approx((-17.0, 8.0))
    assert (bb.min.Y, bb.max.Y) == pytest.approx((-17.0, 43.0))
    assert bb.size.Z == pytest.approx(7.5 + 0.5)


def test_fits_bed(part):
    assert fits_bed(on_bed(part))


def test_bosses_sit_in_the_holes_without_touching_the_board(part):
    board = board_patch(NPOLDA, range(-1, 2), range(-1, 3))
    assert (part & board).volume < 1e-3
    for j in (0, 1):
        hole = Pos(NPOLDA.hole(0, j)) * Cylinder(NPOLDA.hole_d / 2, 20)
        assert (part & hole).volume > 0.1
