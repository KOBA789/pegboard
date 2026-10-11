"""Exporting parts: STEP in board coordinates, STL in print orientation."""

from pathlib import Path

from build123d import Axis, Location, Part, Pos, Shape, export_step, export_stl

# Bambu Lab A1 mini build volume (mm).
BED = (180.0, 180.0, 180.0)

# Fixed STEP header timestamp so regenerating unchanged parts gives byte-identical files.
STEP_TIMESTAMP = "2000-01-01T00:00:00"


def on_bed(part: Part) -> Part:
    """Move an already rotated part so it sits on z = 0, centred on the bed origin."""
    bb = part.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * part


def lay_on_side(part: Part, *, face: str, diagonal: bool = False) -> Part:
    """Rotate so the part's -x or +x face lies on the bed, then place it with on_bed().
    diagonal turns it 45 deg on the bed, for long parts that only fit across the diagonal."""
    part = part.rotate(Axis.Y, {"-x": -90, "+x": 90}[face])
    if diagonal:
        part = part.rotate(Axis.Z, 45)
    return on_bed(part)


def on_face(part: Part, bed: Location) -> Part:
    """Turn the part so its face on the x-y plane of bed (with +z pointing into the part) lies on
    the print bed, then place it with on_bed()."""
    return on_bed(bed.inverse() * part)


def fits_bed(part: Shape, margin: float = 5.0) -> bool:
    size = part.bounding_box().size
    return size.X <= BED[0] - 2 * margin and size.Y <= BED[1] - 2 * margin and size.Z <= BED[2]


def describe(name: str, part: Shape) -> str:
    size = part.bounding_box().size
    return (
        f"{name}: valid={part.is_valid} solids={len(part.solids())} volume={part.volume:.0f} mm^3 "
        f"bbox={size.X:.1f} x {size.Y:.1f} x {size.Z:.1f} mm"
    )


def write_step(shape: Shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    export_step(shape, path, timestamp=STEP_TIMESTAMP)


def write_stl(part: Part, path: Path) -> None:
    """Write a print-ready STL; refuses parts that are broken or larger than the bed."""
    if not part.is_valid or len(part.solids()) != 1:
        raise ValueError(f"{path.name}: not a single valid solid")
    if not fits_bed(part):
        raise ValueError(f"{path.name}: does not fit the {BED[0]:.0f} mm bed")
    path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(part, path, tolerance=0.01, angular_tolerance=0.1)
