"""Parts that go into the pegboard holes, modelled around a single hole.

Every function returns a solid in hole-local board coordinates (hole centre at the origin,
board front face at z = 0, see board.py) that starts `embed` mm inside the part's back plate
(z > 0) so it fuses cleanly. Place it with `Pos(board.hole(i, j)) * solid`.

`flat_width` clips a rod to |x| <= flat_width / 2. The flats let the part be printed lying on
its side (x face on the bed) with the hook bend in the layer plane, which is much stronger
than printing the rod upright. The y-z profile, and so the insertion behaviour checked with
tools/insertion_sim.py, is the same as for the round rod.
"""

import math
from dataclasses import dataclass

from build123d import (
    Box,
    Circle,
    Line,
    Part,
    Plane,
    Pos,
    Solid,
    Sphere,
    ThreePointArc,
    Vector,
    Wire,
    sweep,
)

from .board import Board


@dataclass(frozen=True)
class HookSpec:
    """Bent-rod hook: a straight run through the hole, then an arc curving up behind the board.

    The bend starts inside the board (like the Oculus pegboard hook): with the rod resting on the
    bottom of the hole, the concave side of the bend touches the back edge of the hole, so the
    part cannot float away from the board. lip_gap is the nominal clearance at that edge:
    0.05 = just touching (rigid-body insertion is collision free), negative = preload/tight.
    Defaults are the geometry verified with tools/insertion_sim.py for the phi6 x 5.5 board.
    """

    rod_d: float = 5.0
    bend_r: float = 8.0  # bend radius of the rod centreline
    sweep_deg: float = 60.0
    lip_gap: float = 0.05


def seat_drop(board: Board, rod_d: float) -> float:
    """How far a rod resting on the bottom of a hole sits below the hole centre."""
    return (board.hole_d - rod_d) / 2


def straight_length(board: Board, spec: HookSpec) -> float:
    """Straight run behind the board front face such that the concave side of the bend meets
    the back edge of the hole when the rod sits on the bottom of the hole (plus lip_gap)."""
    r, R = spec.rod_d / 2, spec.bend_r
    hr = board.hole_d / 2
    dy = R - (2 * hr - r)  # arc centre height above the hole's top edge
    dz = math.sqrt((R - r) ** 2 - dy**2)  # horizontal offset centre -> edge on the inner circle
    return board.thickness - dz + spec.lip_gap


def _clip_flats(part: Part | Solid, flat_width: float | None) -> Part | Solid:
    if flat_width is None:
        return part
    return part & Box(flat_width, 1000, 1000)


def bent_hook(
    board: Board,
    spec: HookSpec = HookSpec(),
    *,
    flat_width: float | None = None,
    embed: float = 1.0,
) -> Part:
    """Bent-rod hook with a ball tip. The rod centre sits seat_drop() below the hole centre,
    i.e. resting on the bottom of the hole."""
    r, R = spec.rod_d / 2, spec.bend_r
    a = straight_length(board, spec)
    y0 = -seat_drop(board, spec.rod_d)
    sweep_rad = math.radians(spec.sweep_deg)

    def arc_pt(phi: float) -> Vector:
        return Vector(0, y0 + R - R * math.cos(phi), -(a + R * math.sin(phi)))

    path = Wire(
        [
            Line((0, y0, embed), (0, y0, -a)),
            ThreePointArc(arc_pt(0), arc_pt(sweep_rad / 2), arc_pt(sweep_rad)),
        ]
    )
    profile = Plane(origin=(0, y0, embed), z_dir=(0, 0, -1)) * Circle(r)
    rod = sweep(profile, path=path, is_frenet=True)
    tip = Pos(arc_pt(sweep_rad)) * Sphere(r)
    return _clip_flats(rod + tip, flat_width)


def straight_peg(
    board: Board,
    *,
    rod_d: float = 5.0,
    length: float | None = None,
    chamfer: float = 0.8,
    flat_width: float | None = None,
    embed: float = 1.0,
) -> Part:
    """Plain straight peg on the hole centre with a lead-in chamfer. It only keeps a part from
    swinging about its hooks; length defaults to the board thickness."""
    r = rod_d / 2
    length = board.thickness if length is None else length
    down = Plane(origin=(0, 0, embed), z_dir=(0, 0, -1))
    body = Solid.make_cylinder(r, embed + length - chamfer, down)
    tip = Solid.make_cone(r, r - chamfer, chamfer, down.offset(embed + length - chamfer))
    return _clip_flats(body + tip, flat_width)


def press_fit_peg(
    board: Board,
    *,
    d: float = 6.1,
    length: float = 5.0,
    slot: float = 1.2,
    chamfer: float = 0.8,
    flex: str = "x",
    flat_width: float | None = None,
    embed: float = 1.0,
) -> Part:
    """Straight slotted peg, slightly larger than the hole, for a light press fit. It keeps the
    part from rattling or lifting off its hooks.

    flex is the direction the two halves bend: "x" puts the slot in the y-z plane (the HUB75
    rails, printed with the peg upright), "y" puts it in the x-z plane, which keeps the slot walls
    vertical on a part printed lying on its side. Across the slot the peg is rigid, so the fit
    there is the plain interference of d in the hole. With flats only the top and bottom arcs
    touch the hole, so flex must be "y"."""
    if flat_width is not None and flex != "y":
        raise ValueError("a peg with flats only touches the hole at top and bottom: use flex='y'")
    peg = straight_peg(
        board, rod_d=d, length=length, chamfer=chamfer, flat_width=flat_width, embed=embed
    )
    if flex == "x":
        size, corner = (slot, d + 2), (-slot / 2, -d / 2 - 1)
    else:
        size, corner = (d + 2, slot), (-d / 2 - 1, -slot / 2)
    cut = Solid.make_box(*size, length + 1, Plane.XY.offset(-(length + 1)))
    return peg - Pos(*corner, 0) * cut
