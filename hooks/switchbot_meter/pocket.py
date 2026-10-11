"""Pocket for a SwitchBot 温湿度計 (SwitchBot Meter).

    uv run python -m hooks.switchbot_meter.build

The meter stands in an open-topped box: a floor, side walls up to the top of the back plate
(about 60 % of the meter's height) and a front wall. The front wall is cut down to a low lip
between two ears that cover the outer part of the meter's side bezels, so the display stays
clear. The vents on the meter's top face stay open, and the meter lifts straight out for a
battery change.

The back plate hangs from one bent hook with a slotted press-fit peg 1 pitch below it. It is as
wide as the box and its top is level with the side walls, so the outline is one plain U with no
step; the meter's top stands well above it.

The box stands upright. (The keyboard cradle leans its channel back so the keyboard rests on the
back wall; with clearances of 0.15 the meter has no room to tilt, so the pocket does without.)
It is built from boxes in the meter's frame (origin at the cavity's back bottom edge, y up, z out
along the floor). Every convex edge is rounded by r_soft (pegboard.shape.soft_fillet); the face
against the board stays flat with sharp edges, and the cavity's inner corners stay sharp.

Board coordinates (see src/pegboard/board.py) with the hook hole at the origin; the part is
centred on the hook / peg column. Unlike the keyboard holders it prints standing on its floor,
so the box needs no support, only the hook and the peg sticking out of the back do. The hook bend
then crosses the layers, which is fine for the ~0.5 N it carries. The peg's slot is vertical
(flex="x", as on the HUB75 rails) so it does not bridge: its halves flex sideways, and up and
down it is the plain phi6.1-in-phi6.0 interference.
"""

import copy
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Location,
    Part,
    Polygon,
    Pos,
    Rectangle,
    Rot,
    extrude,
    fillet,
)

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop
from pegboard.export import describe, on_face, write_step, write_stl
from pegboard.shape import bed_cut, board_patch, soft_fillet

from . import meter

OUT = Path(__file__).parent / "output"

P = dict(
    # The hook only pulls with ~0.5 N (meter + part ~1 N, 17 mm out from the board), so the plate
    # can be as thin as the walls.
    plate_t=2.4,
    # plate and wall top above the hook rod centre; insertion_sim.py: 6 OK, 7 NG
    top_above_rod=6.0,
    peg_rows=1,  # the peg goes into the hole this many pitches below the hook
    floor_below_peg=3.0,  # floor top (at the back wall) this far below the peg centre
    floor_t=3.0,
    # each side, all the way to the front: the cavity's sides taper like the meter's (55 -> 54)
    # FDM prints inner sizes ~0.1 small, so do not go much below 0.1
    clear_x=0.15,
    clear_z=0.15,  # front to back
    # side and front walls: 6 lines of a 0.4 nozzle. They carry next to nothing (the meter is
    # ~70 g on the floor); keep them > 2 r_soft, or the two fillets on top meet
    wall_t=2.4,
    # The meter's front bezel is 8 wide all round the display (meter.BEZEL).
    lip_h=8.0,  # front lip above the floor; covers ~7.5 of the bottom bezel (the meter tapers)
    ear_w=6.0,  # ears cover this much of each side bezel, measured from the meter's front edge
    r_window=3.0,  # bottom corners of the cut between the ears, seen from the front
    peg_d=6.1,  # press fit in the phi6.0 hole
    peg_len=5.0,
    peg_slot=1.2,
    r_soft=1.0,  # every convex edge except the board face
)


def frame(p=P) -> tuple[Location, float]:
    """The meter's frame (origin at the cavity's back bottom edge, y up, z out along the floor)
    and the height of the plate and wall tops in it."""
    y_top = -seat_drop(NPOLDA, HookSpec().rod_d) + p["top_above_rod"]
    y_floor = -p["peg_rows"] * NPOLDA.pitch - p["floor_below_peg"]
    return Pos(0, y_floor, p["plate_t"]), y_top - y_floor


def widths(p=P) -> tuple[float, float]:
    """(cavity width at the back, outer width) along x."""
    w_in = meter.WIDTH + 2 * p["clear_x"]
    return w_in, w_in + 2 * p["wall_t"]


def _box(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Part:
    return Pos(x[0], y[0], z[0]) * Box(x[1] - x[0], y[1] - y[0], z[1] - z[0], align=Align.MIN)


def _tapered_cavity(w_back: float, depth: float) -> Part:
    """Cavity in the meter's frame, from the back wall (z = 0) to depth, whose sides close in
    towards the front like the meter's."""
    slope = (meter.WIDTH - meter.FRONT) / 2 / meter.DEPTH  # per side
    a, b = w_back / 2, w_back / 2 - slope * depth
    plan = Polygon((-a, 0), (a, 0), (b, depth), (-b, depth), align=None)  # (x, z) drawn as (x, y)
    # Rot(90, 0, 0) turns the drawing's y into z and the extrusion (+z) into -y
    return Pos(0, 100, 0) * Rot(90, 0, 0) * extrude(plan, 100)


def pocket(p=P) -> Part:
    loc, top = frame(p)
    w_in, w_out = widths(p)
    depth = meter.DEPTH + p["clear_z"]
    reach = depth + p["wall_t"]
    # the floor underside is the bed face, cut back to -floor_t after rounding
    yb = -p["floor_t"] - bed_cut(p["r_soft"])

    # in the meter's frame: the plate's back face is the board face
    outer = _box((-w_out / 2, w_out / 2), (yb, top), (-p["plate_t"], reach))
    cavity = _tapered_cavity(w_in, depth)
    half = meter.FRONT / 2 - p["ear_w"]  # half width of the cut between the ears
    window = Rectangle(2 * half, 100, align=(Align.CENTER, Align.MIN))
    window = fillet(window.vertices().sort_by(Axis.Y)[:2], p["r_window"])
    window = Pos(0, p["lip_h"], depth - 1) * extrude(window, p["wall_t"] + 2)
    body = loc * (outer - cavity - window)
    body = soft_fillet(body, bed=bed_location(p), r=p["r_soft"])
    body += bent_hook(NPOLDA)
    peg = press_fit_peg(NPOLDA, d=p["peg_d"], length=p["peg_len"], slot=p["peg_slot"], flex="x")
    body += Pos(NPOLDA.hole(0, -p["peg_rows"])) * peg
    return body.clean()


def bed_location(p=P) -> Location:
    """The print bed face, the floor underside: its x-y plane, with +z pointing into the part."""
    loc, _ = frame(p)
    return loc * Pos(0, -p["floor_t"], 0) * Rot(-90, 0, 0)


def printed(part: Part, p=P) -> Part:
    """The part as it goes on the print bed: standing on its floor."""
    return on_face(part, bed_location(p))


def meter_placement(p=P) -> Part:
    """Meter model standing in the pocket, its back against the wall and its bottom on the floor."""
    loc, _ = frame(p)
    return loc * meter.model()


def display_view(p=P, grow: float = 0.0) -> Part:
    """The space in front of the placed meter's display (see meter.display_view)."""
    loc, _ = frame(p)
    return loc * meter.display_view(grow)


def build(p=P) -> dict[str, Part]:
    part = pocket(p)
    # children= re-parents the shapes, so the assembly gets its own copies
    board = board_patch(NPOLDA, range(-2, 3), range(-3, 3))
    assembly = Compound(children=[board, copy.copy(part), meter_placement(p)])
    return {"pocket": part, "assembly": assembly}


def main():
    parts = build()
    part = parts["pocket"]
    print(describe("pocket", part))
    write_step(part, OUT / "pocket.step")
    write_step(parts["assembly"], OUT / "pocket_assembly.step")
    write_stl(printed(part), OUT / "pocket.stl")
