from dataclasses import dataclass
from typing import Tuple

from ...enums.team import Team
from . import Piece


@dataclass
class Pawn(Piece):
    max_steps: int = 1

    def moves(self):
        return [
            self.move_left_forward,
            self.move_forward,
            self.move_forward_forward,
            self.move_right_forward,
        ]

    def move_left_forward(self, x: int) -> Tuple[int, int]:
        if self.team == Team.BLACK:
            return (self.x - x, self.y - x)

        if self.team == Team.WHITE:
            return (self.x - x, self.y + x)

        raise RuntimeError(f"Invalid team: {self.team}")

    def move_forward(self, x: int) -> Tuple[int, int]:
        if self.team == Team.BLACK:
            return (self.x, self.y - x)

        if self.team == Team.WHITE:
            return (self.x, self.y + x)

        raise RuntimeError(f"Invalid team: {self.team}")

    def move_forward_forward(self, x: int) -> Tuple[int, int]:
        if self.team == Team.BLACK:
            return (self.x, self.y - x * 2)

        if self.team == Team.WHITE:
            return (self.x, self.y + x * 2)

        raise RuntimeError(f"Invalid team: {self.team}")

    def move_right_forward(self, x: int) -> Tuple[int, int]:
        if self.team == Team.BLACK:
            return (self.x + x, self.y - x)

        if self.team == Team.WHITE:
            return (self.x + x, self.y + x)

        raise RuntimeError(f"Invalid team: {self.team}")
