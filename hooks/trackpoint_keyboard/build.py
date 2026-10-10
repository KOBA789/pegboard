"""Cradle for a ThinkPad TrackPoint Keyboard II standing on its long edge.

    uv run hooks/trackpoint_keyboard/build.py

Two identical cradles, 7 pitches apart, hold the keyboard upright with its bottom face towards
the board and its rear (thick) edge down. Each cradle is a 2D y-z profile (back plate, channel
floor, front lip) extruded along x, hanging from one bent hook with a slotted press-fit peg
2 pitches below it. The peg keeps the cradle from lifting off and rattling when the keyboard is
pulled out.

Every visible edge is rounded by r_soft: the designed shape is shrunk by r_soft (2D offset of the
profile, narrower extrusion, smaller crown radius) and grown back with a 3D offset. The face
against the board stays flat with sharp edges (a rounded edge there leaves a visible gap): the
shape is extended behind the board face and cut flat at z = 0. The -x face on the print bed is
cut the same way, at the depth where the rounding starts at 45 deg, so it prints without supports.

The channel's back wall leans back by `lean_deg` so the keyboard rests against it instead of
balancing on its edge; the front lip stops the bottom edge from sliding out.

Board coordinates (see src/pegboard/board.py) with the hook hole at the origin. The hook and the
peg have flats at x = +-flat_width/2 and the body starts at the -x flat, so the part prints
lying on its -x face with the hook bend in the layer plane.
"""

import copy
import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    Box,
    Compound,
    Cylinder,
    Kind,
    Part,
    Plane,
    Polygon,
    Pos,
    Rot,
    Vector,
    extrude,
    fillet,
    offset,
)

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop
from pegboard.export import describe, lay_on_side, write_step, write_stl

OUT = Path(__file__).parent / "output"

# Lenovo spec (ACC500164 product page): 305.5 x 164 x 13.7 mm, 0.49 kg
KEYBOARD = dict(length=305.5, depth=164.0, height=13.7)
# The long edges are rounded; 2 mm is a conservative guess used only to check the fit.
KEYBOARD_EDGE_R = 2.0

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
    flat_width=4.0,  # hook / peg width between the flats (rod phi5, hole phi6)
    peg_d=6.1,  # press fit in the phi6.0 hole (as on the HUB75 bottom rail)
    peg_len=5.0,
    peg_slot=1.2,
    # profile corner radii
    r_in=1.5,  # channel inner corners (wall/floor, floor/lip)
    r_top=3.0,  # plate top, front
    r_lip=1.9,  # lip top, both corners (nearly a full round on the 4 mm lip)
    r_heel=6.0,  # lip outer bottom
    r_crown=4.0,  # plate top corners seen from the front; must clear the hook at the -x flat
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

    # shrink by r (the bed side is extended by the 45 deg cut depth), then grow back by r
    x0 = -p["flat_width"] / 2
    bed_cut = r * (1 - math.cos(math.radians(45)))
    core = Plane.YZ * offset(face, -r)  # Plane.YZ maps local (u, v) to global (y, z)
    core = Pos(x0 - bed_cut + r, 0, 0) * extrude(core, p["width"] + bed_cut - 2 * r)
    core &= crown_prism(core.bounding_box(), p["r_crown"] - r)
    body = offset(core, r, kind=Kind.ARC)
    body &= Pos(x0, -500, 0) * Box(1000, 1000, 1000, align=Align.MIN)

    body += bent_hook(NPOLDA, flat_width=p["flat_width"])
    peg = press_fit_peg(
        NPOLDA, d=p["peg_d"], length=p["peg_len"], slot=p["peg_slot"], flat_width=p["flat_width"]
    )
    body += Pos(NPOLDA.hole(0, -p["peg_rows"])) * peg
    return body.clean()


def crown_prism(bb, radius) -> Part:
    """Prism along z of the front view of bb, with the two top corners rounded."""
    pts = [(bb.min.X, bb.min.Y), (bb.max.X, bb.min.Y), (bb.max.X, bb.max.Y), (bb.min.X, bb.max.Y)]
    outline = Polygon(*pts, align=None)
    outline = fillet(outline.vertices().filter_by_position(Axis.Y, bb.max.Y, bb.max.Y), radius)
    return Pos(0, 0, bb.min.Z - 1) * extrude(outline, bb.size.Z + 2)


def keyboard_placement(p=P):
    """Keyboard model resting in the left cradle's channel, and the z of its back face at the top
    edge (its clearance to the board)."""
    _, corner = profile_points(p)
    kb = KEYBOARD
    th = p["lean_deg"]
    box = Box(kb["length"], kb["depth"], kb["height"], align=Align.MIN)
    box = fillet(box.edges().filter_by(Axis.X), KEYBOARD_EDGE_R)
    x_mid = (NPOLDA.hole(p["spacing"], 0).X) / 2 - p["flat_width"] / 2 + p["width"] / 2
    placed = Pos(x_mid - kb["length"] / 2, corner.X, corner.Y) * Rot(-th, 0, 0) * box
    top_back_z = corner.Y - kb["depth"] * math.sin(math.radians(th))
    return placed, top_back_z


def board_patch(p=P) -> Part:
    """A piece of pegboard around the cradles, for the assembly view."""
    pitch, t = NPOLDA.pitch, NPOLDA.thickness
    cols, rows = range(-6, p["spacing"] + 7), range(-4, 8)
    w, h = len(cols) * pitch, len(rows) * pitch
    x0, y0 = cols[0] * pitch - pitch / 2, rows[0] * pitch - pitch / 2
    patch = Pos(x0 + w / 2, y0 + h / 2, -t / 2) * Box(w, h, t)
    for i in cols:
        for j in rows:
            patch -= Pos(NPOLDA.hole(i, j) + Vector(0, 0, -t / 2)) * Cylinder(NPOLDA.hole_d / 2, t)
    return patch


def build(p=P) -> dict[str, Part]:
    part = cradle(p)
    kb, _ = keyboard_placement(p)
    # children= re-parents the shapes, so the assembly gets its own copies
    left = copy.copy(part)
    right = Pos(NPOLDA.hole(p["spacing"], 0)) * part
    assembly = Compound(children=[board_patch(p), left, right, kb])
    return {"cradle": part, "assembly": assembly}


def main():
    parts = build()
    cradle_part = parts["cradle"]
    print(describe("cradle", cradle_part))
    _, top_z = keyboard_placement()
    print(f"keyboard top edge clears the board by {top_z:.1f} mm")
    write_step(cradle_part, OUT / "cradle.step")
    write_step(parts["assembly"], OUT / "assembly.step")
    write_stl(lay_on_side(cradle_part, face="-x"), OUT / "cradle.stl")


if __name__ == "__main__":
    main()
