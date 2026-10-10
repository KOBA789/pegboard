"""Cradle for a ThinkPad TrackPoint Keyboard II standing on its long edge (option A).

    uv run python -m hooks.trackpoint_keyboard.build

Two identical cradles, 7 pitches apart, hold the keyboard upright with its bottom face towards
the board and its rear (thick) edge down. Each cradle is a 2D y-z profile (back plate, channel
floor, front lip) extruded along x, hanging from one bent hook with a slotted press-fit peg
2 pitches below it. The peg keeps the cradle from lifting off and rattling when the keyboard is
pulled out.

Every visible edge is rounded by r_soft (pegboard.shape.soft_extrude); the face against the board
stays flat with sharp edges, and the -x face on the print bed starts its rounding at 45 deg.

The channel's back wall leans back by `lean_deg` so the keyboard rests against it instead of
balancing on its edge; the front lip stops the bottom edge from sliding out.

Board coordinates (see src/pegboard/board.py) with the hook hole at the origin. The body is
centred on the hook / peg column so the board face bears on both sides of it, which stops the
part twisting sideways; the round hook and the peg (tight in x, its halves flex in y) stop it
shifting and rotating in the board plane. It prints lying on its -x face with the hook bend in the
layer plane; the hook and the peg then hang mid-height and need a little support.
"""

import copy
import math
from pathlib import Path

from build123d import Compound, Part, Polygon, Pos, Rot, Vector, fillet

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop
from pegboard.export import describe, lay_on_side, write_step, write_stl
from pegboard.shape import board_patch, soft_extrude

from . import keyboard

OUT = Path(__file__).parent / "output"

P = dict(
    width=15.0,  # cradle width along x
    plate_t=5.0,  # back plate thickness
    # plate top above the hook rod centre; insertion_sim.py: 6 OK, 7 NG (plate hits the board)
    top_above_rod=6.0,
    peg_rows=2,  # the peg goes into the hole this many pitches below the hook
    floor_below_peg=4.0,  # channel floor (at the back wall) this far below the peg centre
    gap=16.0,  # channel width, keyboard height 13.7 + clearance
    floor_t=4.0,
    lip_t=4.0,
    lip_h=15.0,  # lip height above the channel floor
    lean_deg=2.0,  # back wall lean; the keyboard's top must stay clear of the board
    peg_d=6.1,  # press fit in the phi6.0 hole (as on the HUB75 bottom rail)
    peg_len=5.0,
    peg_slot=1.2,
    # profile corner radii
    r_in=1.5,  # channel inner corners (wall/floor, floor/lip)
    r_top=3.0,  # plate top, front
    r_lip=1.9,  # lip top, both corners (nearly a full round on the 4 mm lip)
    r_heel=6.0,  # lip outer bottom
    r_crown=4.0,  # plate top corners seen from the front
    r_soft=1.5,  # every other visible edge
    spacing=7,  # pitches between the two cradles
)


def profile_points(p=P, z_back=0.0) -> tuple[list[tuple[float, float]], Vector]:
    """Outline of the y-z profile as (y, z) pairs with its back side at z_back, and the (y, z)
    corner where the channel's back wall meets its floor."""
    th = math.radians(p["lean_deg"])
    up = Vector(math.cos(th), -math.sin(th))  # along the back wall, upwards
    out = Vector(math.sin(th), math.cos(th))  # channel floor direction, away from the wall
    y_top = -seat_drop(NPOLDA, HookSpec().rod_d) + p["top_above_rod"]
    y_floor = -p["peg_rows"] * NPOLDA.pitch - p["floor_below_peg"]
    T = p["plate_t"]
    corner = Vector(y_floor, T + (y_top - y_floor) * math.tan(th))  # wall meets floor
    lip_in = corner + out * p["gap"]
    lip_out = lip_in + out * p["lip_t"]
    under = lip_out - up * p["floor_t"]  # outer bottom of the lip
    back = Vector(under.X - (under.Y - z_back) * math.tan(th), z_back)  # underside meets z_back
    pts = [
        Vector(y_top, z_back),
        Vector(y_top, T),
        corner,
        lip_in,
        lip_in + up * p["lip_h"],
        lip_out + up * p["lip_h"],
        under,
        back,
    ]
    return [(v.X, v.Y) for v in pts], corner


def cradle(p=P) -> Part:
    r = p["r_soft"]
    # profile in local (u, v) = (y, z), extended behind the board face so the cut there is sharp
    pts, _ = profile_points(p, z_back=-r)
    face = Polygon(*pts, align=None)
    # outline order: plate top back, plate top front, wall/floor, floor/lip, lip top inner,
    # lip top outer, lip outer bottom, floor underside behind the board
    radii = [None, "r_top", "r_in", "r_in", "r_lip", "r_lip", "r_heel", None]
    for q, name in zip(pts, radii, strict=True):
        if name:
            face = fillet(face.vertices().sort_by_distance(Vector(*q))[:1], p[name])

    x0 = -p["width"] / 2  # centred on the hook / peg column, so the board face bears on both sides
    body = soft_extrude(face, x0=x0, width=p["width"], r=r, crown_r=p["r_crown"])

    body += bent_hook(NPOLDA)
    peg = press_fit_peg(NPOLDA, d=p["peg_d"], length=p["peg_len"], slot=p["peg_slot"], flex="y")
    body += Pos(NPOLDA.hole(0, -p["peg_rows"])) * peg
    return body.clean()


def keyboard_placement(p=P):
    """Keyboard model resting in the left cradle's channel, and the z of its back face at the top
    edge (its clearance to the board)."""
    _, corner = profile_points(p)
    th = p["lean_deg"]
    x_mid = NPOLDA.hole(p["spacing"], 0).X / 2
    placed = (
        Pos(x_mid - keyboard.LENGTH / 2, corner.X, corner.Y)
        * Rot(-th, 0, 0)
        * keyboard.model(standing=True)
    )
    top_back_z = corner.Y - keyboard.DEPTH * math.sin(math.radians(th))
    return placed, top_back_z


def build(p=P) -> dict[str, Part]:
    part = cradle(p)
    kb, _ = keyboard_placement(p)
    # children= re-parents the shapes, so the assembly gets its own copies
    left = copy.copy(part)
    right = Pos(NPOLDA.hole(p["spacing"], 0)) * part
    board = board_patch(NPOLDA, range(-6, p["spacing"] + 7), range(-4, 8))
    assembly = Compound(children=[board, left, right, kb])
    return {"cradle": part, "assembly": assembly}


def main():
    parts = build()
    cradle_part = parts["cradle"]
    print(describe("cradle", cradle_part))
    _, top_z = keyboard_placement()
    print(f"keyboard top edge clears the board by {top_z:.1f} mm")
    write_step(cradle_part, OUT / "cradle.step")
    write_step(parts["assembly"], OUT / "cradle_assembly.step")
    write_stl(lay_on_side(cradle_part, face="-x"), OUT / "cradle.stl")
