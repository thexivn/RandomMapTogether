from dataclasses import dataclass
from . import Piece


@dataclass
class Bishop(Piece):
    def moves(self):
        return [
            self.move_left_up,
            self.move_right_up,
            self.move_right_down,
            self.move_left_down,
        ]

    def move_left_up(self, x):
        return (self.x - x, self.y + x)

    def move_right_up(self, x):
        return (self.x + x, self.y + x)

    def move_right_down(self, x):
        return (self.x + x, self.y - x)

    def move_left_down(self, x):
        return (self.x - x, self.y - x)
