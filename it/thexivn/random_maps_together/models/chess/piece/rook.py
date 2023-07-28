from dataclasses import dataclass
from . import Piece


@dataclass
class Rook(Piece):
    def moves(self):
        return [
            self.move_left,
            self.move_up,
            self.move_right,
            self.move_down,
        ]

    def move_left(self, x):
        return (self.x - x, self.y)

    def move_up(self, x):
        return (self.x, self.y + x)

    def move_right(self, x):
        return (self.x + x, self.y)

    def move_down(self, x):
        return (self.x, self.y - x)
