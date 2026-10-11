"""Slide-in holder for an iPad Pro 11 in landscape, close to the board, USB-C on the right.

    uv run python -m hooks.ipad_pro_11.build

Two parts carry the iPad a plate's thickness in front of the board:

* stop (left): holds the bottom left of the iPad. A channel along the bottom edge, and a second
  channel up the left edge whose side wall is the stop the iPad slides against. The left channel's
  front lip keeps the top from tipping forward; the bottom lip keeps the bottom from kicking out.
* rail (right): the same bottom channel, open at both ends, near the right edge of the board.

The iPad goes in from the right: bottom edge into the rail, slide left until its left edge meets
the stop. To take it out, pinch the right edge, which overhangs the end of the board, and slide it
out to the right. Nothing touches the top edge (Apple Pencil) or the right edge (USB-C).

The iPad's back rests on the plates, so its back face is plate_t in front of the board and the
rear camera bump stays clear of it. The parts are plates behind the iPad with a channel profile
at the bottom: the board face is flat and sharp-edged, every other convex edge is rounded by
r_soft. Each hangs from one bent hook with a slotted press-fit peg below it, centred on that
column, and prints lying on its -x face with the hook bend in the layer plane.

Board coordinates (see src/pegboard/board.py) with the stop's hook hole at the origin; each part
is built around its own hook hole.
"""

import copy
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Location,
    Part,
    Plane,
    Polygon,
    Pos,
    Vector,
    extrude,
    fillet,
)

from pegboard import NPOLDA, HookSpec, bent_hook, press_fit_peg, seat_drop
from pegboard.export import describe, lay_on_side, write_step, write_stl
from pegboard.shape import bed_cut, board_patch, soft_extrude, soft_fillet

from . import ipad

OUT = Path(__file__).parent / "output"

P = dict(
    plate_t=3.5,  # the iPad's back is this far from the board; camera bump 1.5 (estimate)
    # plate top above the hook rod centre; insertion_sim.py: 6 OK, 7 NG (plate hits the board)
    top_above_rod=6.0,
    gap=ipad.THICKNESS + 0.8,  # channel width; FDM prints inner sizes ~0.1 mm small
    lip_h=6.0,  # bottom lip height above the floor; inside the ~8.9 mm display border (estimate)
    lip_t=2.4,  # front lip thickness (z)
    floor_t=4.0,
    # rail (right)
    rail_width=20.0,
    rail_peg_rows=1,  # its peg goes this many pitches below its hook
    floor_below_peg=5.0,  # the rail's floor (the iPad's bottom edge) below its peg centre
    spacing=8,  # pitches from the stop's hook column to the rail's
    # stop (left)
    stop_rows=3,  # the stop's hook is this many pitches above the rail's
    stop_peg_rows=3,  # its peg goes this many pitches below its hook (level with the rail's hook)
    stop_width=26.0,
    side_t=3.0,  # side wall (the stop) thickness
    lip_w=6.0,  # left lip reach over the display border, from the stop face
    # the stop face touches the left edge only in this band above the bottom edge (mm): the middle
    # of the edge, clear of the speaker grilles and the top button (positions not checked)
    pad=(79.0, 99.0),
    peg_d=6.1,  # press fit in the phi6.0 hole
    peg_len=5.0,
    peg_slot=1.2,
    # corner radii
    r_in=0.5,  # channel inner corners, small so the iPad's edge sits down on the floor
    r_lip=1.1,  # lip top, both corners (nearly a full round on the 2.4 mm lip)
    r_soft=0.8,  # every other visible edge; less than lip_t / 2
)


def y_top(p=P) -> float:
    return -seat_drop(NPOLDA, HookSpec().rod_d) + p["top_above_rod"]


def rail_floor(p=P) -> float:
    """y of the channel floor (the iPad's bottom edge) relative to the rail's hook hole."""
    return -p["rail_peg_rows"] * NPOLDA.pitch - p["floor_below_peg"]


def stop_floor(p=P) -> float:
    """The same floor relative to the stop's hook hole."""
    return rail_floor(p) - p["stop_rows"] * NPOLDA.pitch


def stop_face(p=P) -> float:
    """x of the stop face (the iPad's left edge) relative to the stop's hook hole."""
    return -p["stop_width"] / 2 + p["side_t"]


def channel_profile(y_floor: float, p=P, *, z_back=0.0, radii=True):
    """y-z profile of a plate from y_top() down to a channel at y_floor, as a face in local
    (u, v) = (y, z), and its outline points. The back side is at z_back."""
    T, g, lt = p["plate_t"], p["gap"], p["lip_t"]
    z_lip = T + g
    pts = [
        (y_top(p), z_back),
        (y_top(p), T),
        (y_floor, T),  # back of the channel meets the floor
        (y_floor, z_lip),  # floor meets the lip
        (y_floor + p["lip_h"], z_lip),
        (y_floor + p["lip_h"], z_lip + lt),
        (y_floor - p["floor_t"], z_lip + lt),
        (y_floor - p["floor_t"], z_back),
    ]
    face = Polygon(*pts, align=None)
    if radii:
        names = [None, None, "r_in", "r_in", "r_lip", "r_lip", None, None]
        for q, name in zip(pts, names, strict=True):
            if name:
                face = fillet(face.vertices().sort_by_distance(Vector(*q))[:1], p[name])
    return face, pts


def _mounts(body: Part, peg_rows: int, p=P) -> Part:
    body += bent_hook(NPOLDA)
    peg = press_fit_peg(NPOLDA, d=p["peg_d"], length=p["peg_len"], slot=p["peg_slot"], flex="y")
    body += Pos(NPOLDA.hole(0, -peg_rows)) * peg
    return body.clean()


def rail(p=P) -> Part:
    r = p["r_soft"]
    face, _ = channel_profile(rail_floor(p), p, z_back=-r)
    # the plate top corner is rounded by soft_extrude itself (r_soft)
    body = soft_extrude(face, x0=-p["rail_width"] / 2, width=p["rail_width"], r=r)
    return _mounts(body, p["rail_peg_rows"], p)


def stop(p=P) -> Part:
    r = p["r_soft"]
    T, g, lt = p["plate_t"], p["gap"], p["lip_t"]
    x0 = -p["stop_width"] / 2
    xb = x0 - bed_cut(r)  # built past the bed face, cut back by soft_fillet
    xs = stop_face(p)
    yf = stop_floor(p)
    yb, yt = yf - p["floor_t"], y_top(p)

    # sharp inner corners here: the window cuts meet them; soft_fillet rounds the convex edges
    face, _ = channel_profile(yf, p, radii=False)
    body = Pos(xb, 0, 0) * extrude(Plane.YZ * face, p["stop_width"] / 2 - xb)
    # left channel: side wall (the stop) and the front lip over the display border
    side = Pos(xb, yb, 0) * Box(xs - xb, yt - yb, T + g + lt, align=Align.MIN)
    lip = Pos(xb, yb, T + g) * Box(xs + p["lip_w"] - xb, yt - yb, lt, align=Align.MIN)
    body = body + side + lip
    # open the side wall in front of the left edge, except for the pad the iPad stops against
    lo, hi = yf + p["pad"][0], yf + p["pad"][1]
    for y0, y1 in ((yf, lo), (hi, yt + 1)):
        body -= Pos(xb - 1, y0, T) * Box(xs - xb + 1, y1 - y0, g, align=Align.MIN)
    body = soft_fillet(body, bed=bed_location(p), r=r)
    return _mounts(body, p["stop_peg_rows"], p)


def bed_location(p=P) -> Location:
    """The stop's print bed face, its -x side: its x-y plane, with +z pointing into the part."""
    return Plane(origin=(-p["stop_width"] / 2, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)).location


def stop_hole(p=P) -> Vector:
    return NPOLDA.hole(0, 0)


def rail_hole(p=P) -> Vector:
    return NPOLDA.hole(p["spacing"], -p["stop_rows"])


def ipad_placement(p=P) -> tuple[Part, Part]:
    """iPad model (and its camera bump) in place: on the floor, back on the plates, left edge
    against the stop."""
    loc = Pos(stop_face(p), stop_floor(p), p["plate_t"])
    return loc * ipad.model(), loc * ipad.camera()


def build(p=P) -> dict[str, Part]:
    stop_part, rail_part = stop(p), rail(p)
    pad, cam = ipad_placement(p)
    # children= re-parents the shapes, so the assembly gets its own copies
    left = copy.copy(stop_part)
    right = Pos(rail_hole(p)) * rail_part
    board = board_patch(NPOLDA, range(-3, p["spacing"] + 1), range(-p["stop_rows"] - 3, 5))
    assembly = Compound(children=[board, left, right, pad + cam])
    return {"stop": stop_part, "rail": rail_part, "assembly": assembly}


def main():
    parts = build()
    for name in ("stop", "rail"):
        print(describe(name, parts[name]))
    pad, _ = ipad_placement()
    over = pad.bounding_box().max.X - rail_hole().X
    print(f"the iPad reaches {over:.1f} mm right of the rail's hook column")
    print(f"front of the lips: {P['plate_t'] + P['gap'] + P['lip_t']:.1f} mm from the board")
    for name in ("stop", "rail"):
        write_step(parts[name], OUT / f"{name}.step")
        write_stl(lay_on_side(parts[name], face="-x"), OUT / f"{name}.stl")
    write_step(parts["assembly"], OUT / "holder_assembly.step")
