from dataclasses import dataclass
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

    def move_left_forward(self, x):
        if self.team == Team.BLACK:
            return (self.x - x, self.y - x)
        elif self.team == Team.WHITE:
            return (self.x - x, self.y + x)

    def move_forward(self, x):
        if self.team == Team.BLACK:
            return (self.x, self.y - x)
        elif self.team == Team.WHITE:
            return (self.x, self.y + x)

    def move_forward_forward(self, x):
        if self.team == Team.BLACK:
            return (self.x, self.y - x * 2)
        elif self.team == Team.WHITE:
            return (self.x, self.y + x * 2)

    def move_right_forward(self, x):
        if self.team == Team.BLACK:
            return (self.x + x, self.y - x)
        elif self.team == Team.WHITE:
            return (self.x + x, self.y + x)
