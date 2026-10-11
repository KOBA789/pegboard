"""Build the spacer plate into ./output/.

    uv run python -m hooks.plate.build

Not a hook: a plain plate that goes between the pegboard and its pole, so a desk light can clamp
the pole and the board together. Two low bosses on the face against the board drop into two
holes of one column and locate it.

The plate stands portrait behind the board. Seen from the room (looking at the boss face through
the board), the lower boss is 8 mm left of the right edge and 17 mm above the bottom edge, and
the upper one is one pitch above it.

Board coordinates (see src/pegboard/board.py) with the lower boss's hole at the origin: the plate
lies against the board's back face, z = -thickness of the board, and the bosses rise into the
holes towards +z. Edges stay sharp. It prints on its back face with the bosses on top.
"""

from pathlib import Path

from build123d import Align, Box, Cylinder, Part, Pos

from pegboard import NPOLDA
from pegboard.export import describe, on_bed, write_step, write_stl

OUT = Path(__file__).parent / "output"

P = dict(
    width=25.0,  # x, nominal (requested)
    height=60.0,  # y, nominal (requested)
    thickness=7.5,  # z, nominal (requested)
    boss_right=8.0,  # lower boss centre from the right edge, nominal (requested)
    boss_bottom=17.0,  # lower boss centre from the bottom edge, nominal (requested)
    boss_h=0.5,  # nominal (requested)
    boss_d=NPOLDA.hole_d - 0.2,  # 0.1 clearance per side in the measured phi6.0 hole
    boss_rows=2,  # bosses one pitch apart, upwards
)


def plate() -> Part:
    back = -NPOLDA.thickness  # the board's back face
    x0 = P["boss_right"] - P["width"]
    y0 = -P["boss_bottom"]
    part = Pos(x0, y0, back) * Box(
        P["width"], P["height"], P["thickness"], align=(Align.MIN, Align.MIN, Align.MAX)
    )
    for j in range(P["boss_rows"]):
        part += Pos(NPOLDA.hole(0, j) + (0, 0, back)) * Cylinder(
            P["boss_d"] / 2, P["boss_h"], align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return part


def main():
    part = plate()
    print(describe("plate", part))
    write_step(part, OUT / "plate.step")
    write_stl(on_bed(part), OUT / "plate.stl")


if __name__ == "__main__":
    main()
