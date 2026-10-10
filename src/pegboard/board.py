"""Pegboard dimensions.

Board coordinate system (shared by every hook in this repo):
    x : along the board, right when facing it
    y : up
    z : out of the board towards the room; z = 0 is the board's front face
    origin : centre of a reference hole
Hooks and pegs therefore grow into -z, and whatever they hold sits at +z.
"""

from dataclasses import dataclass

from build123d import Vector


@dataclass(frozen=True)
class Board:
    pitch: float
    hole_d: float
    thickness: float

    def hole(self, i: int, j: int) -> Vector:
        """Centre of the hole i pitches right and j pitches up from the reference hole."""
        return Vector(i * self.pitch, j * self.pitch, 0)


# Nitori 突っ張り壁面収納パンチングボード Nポルダ (see docs/nitori_npolda.md).
# The catalogue says phi5 holes; the real holes measure phi6.0 and the board 5.5 thick.
NPOLDA = Board(pitch=25.0, hole_d=6.0, thickness=5.5)
