from dataclasses import dataclass
from . import Piece


@dataclass
class King(Piece):
    max_steps: 1

    def moves(self):
        return [
            self.move_left,
            self.move_left_up,
            self.move_up,
            self.move_right_up,
            self.move_right,
            self.move_right_down,
            self.move_down,
            self.move_left_down,
        ]

    def move_left(self, x):
        return (self.x - x, self.y)

    def move_left_up(self, x):
        return (self.x - x, self.y + x)

    def move_up(self, x):
        return (self.x, self.y + x)

    def move_right_up(self, x):
        return (self.x + x, self.y + x)

    def move_right(self, x):
        return (self.x + x, self.y)

    def move_right_down(self, x):
        return (self.x + x, self.y - x)

    def move_down(self, x):
        return (self.x, self.y - x)

    def move_left_down(self, x):
        return (self.x - x, self.y - x)
