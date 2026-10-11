"""Shelf brackets for a ThinkPad TrackPoint Keyboard II lying flat (option B).

    uv run python -m hooks.trackpoint_keyboard.build

Two identical cantilever brackets, 7 pitches apart, carry the keyboard flat on their top edges
with its rear edge at the board. Modelled on the Oculus controller hook
(https://makerworld.com/en/models/14175-pegboard-mounts-for-oculus-meta-quest-2): a deep root that
hangs from a bent hook at the top and bears on the board at the bottom, tapering towards the tip,
with an upturned lip at the front. A slotted press-fit peg 1 pitch below the hook keeps the bracket
from lifting off when the keyboard is picked up.

The arm's underside is a concave sweep, depth(z) = tip_t + (arm_root - tip_t) *
(1 - z / length) ** taper, deep where the bending moment is largest. As on the Oculus hook, a
foot runs down the board below it (square to the board, so no thin edge to chip) and blends into
the sweep with a concave radius, and the tip is rounded into a claw: a large radius under the lip
and a round lip top. Everything else keeps sharp edges (rounded edges all over looked too soft).

Board coordinates (see src/pegboard/board.py) with the hook hole at the origin. Like the cradle,
the profile is extruded along x centred on the hook / peg column (see cradle.py for why) and the
part prints lying on its -x face with support under the hook and the peg; it is ~183 mm long,
so it goes diagonally on the 180 mm bed.
"""

import copy
from pathlib import Path

from build123d import (
    Compound,
    Face,
    Line,
    Part,
    Plane,
    Pos,
    Spline,
    Vector,
    Wire,
    extrude,
    fillet,
    make_face,
)

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop
from pegboard.export import describe, lay_on_side, write_step, write_stl
from pegboard.shape import board_patch

from . import keyboard

OUT = Path(__file__).parent / "output"

P = dict(
    width=15.0,  # bracket width along x
    # shelf surface = plate top, above the hook rod centre; insertion_sim.py: 6 OK, 7 NG
    top_above_rod=6.0,
    peg_rows=1,  # the peg goes into the hole this many pitches below the hook
    foot_below_peg=8.0,  # bottom of the foot this far below the peg centre
    foot_t=6.0,  # foot thickness off the board (Oculus hook: 6)
    reach=166.0,  # lip inner face from the board: keyboard depth 164 + clearance
    arm_root=30.0,  # depth of the underside curve extended to the board (shelf to peg level)
    tip_t=6.0,  # arm depth under the lip
    taper=2.0,  # underside curve: 1 = straight, larger = deeper near the board, slimmer outside
    lip_t=4.0,
    lip_h=6.0,  # lip height above the shelf surface
    peg_d=6.1,  # press fit in the phi6.0 hole
    peg_len=5.0,
    peg_slot=1.2,
    # profile corner radii; all other corners stay sharp
    r_root=6.0,  # concave blend from the foot into the underside
    r_in=1.5,  # shelf / lip inner corner
    r_lip=1.9,  # lip top, both corners: nearly a full round on the 4 mm lip
    r_heel=8.0,  # under the lip, sweeping up into the claw
    spacing=7,  # pitches between the two brackets
)


def levels(p=P) -> tuple[float, float]:
    """(shelf surface y, foot bottom y)."""
    y_top = -seat_drop(NPOLDA, HookSpec().rod_d) + p["top_above_rod"]
    y_bot = -p["peg_rows"] * NPOLDA.pitch - p["foot_below_peg"]
    return y_top, y_bot


def profile(p=P) -> Face:
    """y-z outline in local (u, v) = (y, z)."""
    y_top, y_bot = levels(p)
    z_lip = p["reach"]
    z_end = z_lip + p["lip_t"]
    root, tip, k = p["arm_root"], p["tip_t"], p["taper"]

    def underside(z: float) -> Vector:
        return Vector(y_top - (tip + (root - tip) * (1 - z / z_end) ** k), z)

    # (y, z) corners going round from the plate top at the board, with their radii
    corners = [
        (Vector(y_top, 0), None),
        (Vector(y_top, z_lip), "r_in"),
        (Vector(y_top + p["lip_h"], z_lip), "r_lip"),
        (Vector(y_top + p["lip_h"], z_end), "r_lip"),
        (underside(z_end), "r_heel"),
        (underside(p["foot_t"]), "r_root"),  # the sweep meets the foot's front face
        (Vector(y_bot, p["foot_t"]), None),
        (Vector(y_bot, 0), None),
    ]
    pts = [q for q, _ in corners]
    n = 24
    sweep_pts = [underside(z_end + (p["foot_t"] - z_end) * i / n) for i in range(n + 1)]
    edges = [Line(a, b) for a, b in zip(pts[:5], pts[1:5], strict=False)]
    edges += [Spline(*sweep_pts)]  # tip -> foot
    edges += [Line(a, b) for a, b in zip(pts[5:], pts[6:] + pts[:1], strict=False)]
    face = make_face(Wire(edges))
    for q, name in corners:
        if name:
            face = fillet(face.vertices().sort_by_distance(q)[:1], p[name])
    return face


def bracket(p=P) -> Part:
    x0 = -p["width"] / 2  # centred on the hook / peg column, so the board face bears on both sides
    body = Pos(x0, 0, 0) * extrude(Plane.YZ * profile(p), p["width"])  # local (u, v) = (y, z)
    body += bent_hook(NPOLDA)
    peg = press_fit_peg(NPOLDA, d=p["peg_d"], length=p["peg_len"], slot=p["peg_slot"], flex="y")
    body += Pos(NPOLDA.hole(0, -p["peg_rows"])) * peg
    return body.clean()


def keyboard_placement(p=P) -> Part:
    """Keyboard model lying on the shelves, its rear edge 0.5 mm off the board."""
    y_top, _ = levels(p)
    x_mid = NPOLDA.hole(p["spacing"], 0).X / 2
    return Pos(x_mid - keyboard.LENGTH / 2, y_top, 0.5) * keyboard.model()


def build(p=P) -> dict[str, Part]:
    part = bracket(p)
    # children= re-parents the shapes, so the assembly gets its own copies
    left = copy.copy(part)
    right = Pos(NPOLDA.hole(p["spacing"], 0)) * part
    board = board_patch(NPOLDA, range(-6, p["spacing"] + 7), range(-4, 4))
    assembly = Compound(children=[board, left, right, keyboard_placement(p)])
    return {"shelf": part, "assembly": assembly}


def main():
    parts = build()
    part = parts["shelf"]
    print(describe("shelf", part))
    write_step(part, OUT / "shelf.step")
    write_step(parts["assembly"], OUT / "shelf_assembly.step")
    write_stl(lay_on_side(part, face="-x", diagonal=True), OUT / "shelf.stl")
