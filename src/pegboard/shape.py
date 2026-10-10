"""Body shaping shared by hooks: rounded extrusions of a y-z profile, and a board for assemblies."""

import math

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Face,
    Kind,
    Part,
    Plane,
    Polygon,
    Pos,
    Vector,
    extrude,
    fillet,
    offset,
)

from .board import Board

# A rounded edge starting at this angle from the bed prints without supports.
BED_ANGLE_DEG = 45.0


def soft_extrude(
    profile: Face, *, x0: float, width: float, r: float, crown_r: float | None = None
) -> Part:
    """Extrude a y-z profile along +x from x0 by width, with every visible edge rounded by r.

    profile is drawn in local (u, v) = (y, z) coordinates, with its back side extended to z = -r
    behind the board face. Use only lines and arcs: the 3D offset fails on B-spline edges.
    Rounding works by shrinking the shape by r (2D offset of the profile, narrower extrusion,
    smaller crown) and growing it back with a 3D offset, which is far more robust than filleting
    the edges one by one. The result is then cut flat:
      * at z = 0, so the face against the board keeps sharp edges (no visible gap at the board);
      * at x = x0, the face on the print bed, where the rounding starts at BED_ANGLE_DEG.
    crown_r rounds the two top corners seen from the front (x-y view).
    """
    bed_cut = r * (1 - math.cos(math.radians(BED_ANGLE_DEG)))
    core = Plane.YZ * offset(profile, -r)  # Plane.YZ maps local (u, v) to global (y, z)
    core = Pos(x0 - bed_cut + r, 0, 0) * extrude(core, width + bed_cut - 2 * r)
    if crown_r is not None:
        core &= crown_prism(core.bounding_box(), crown_r - r)
    body = offset(core, r, kind=Kind.ARC)
    return body & Pos(x0, -500, 0) * Box(1000, 1000, 1000, align=Align.MIN)


def crown_prism(bb, radius: float) -> Part:
    """Prism along z of the front view of bb, with the two top corners rounded."""
    pts = [(bb.min.X, bb.min.Y), (bb.max.X, bb.min.Y), (bb.max.X, bb.max.Y), (bb.min.X, bb.max.Y)]
    outline = Polygon(*pts, align=None)
    outline = fillet(outline.vertices().filter_by_position(Axis.Y, bb.max.Y, bb.max.Y), radius)
    return Pos(0, 0, bb.min.Z - 1) * extrude(outline, bb.size.Z + 2)


def board_patch(board: Board, cols: range, rows: range) -> Part:
    """A piece of pegboard covering the holes (i, j) in cols x rows, for assembly views."""
    pitch, t = board.pitch, board.thickness
    w, h = len(cols) * pitch, len(rows) * pitch
    x0, y0 = cols[0] * pitch - pitch / 2, rows[0] * pitch - pitch / 2
    patch = Pos(x0 + w / 2, y0 + h / 2, -t / 2) * Box(w, h, t)
    for i in cols:
        for j in rows:
            patch -= Pos(board.hole(i, j) + Vector(0, 0, -t / 2)) * Cylinder(board.hole_d / 2, t)
    return patch
