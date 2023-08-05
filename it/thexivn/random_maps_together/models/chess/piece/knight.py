from dataclasses import dataclass
from . import Piece


@dataclass
class Knight(Piece):
    max_steps: int = 1

    def moves(self):
        return [
            self.move_left_up_left,
            self.move_left_up_up,
            self.move_right_up_up,
            self.move_right_up_right,
            self.move_right_down_right,
            self.move_right_down_down,
            self.move_left_down_down,
            self.move_left_down_left,
        ]

    def move_left_up_left(self, x):
        return (self.x - x * 2, self.y + x)

    def move_left_up_up(self, x):
        return (self.x - x, self.y + x * 2)

    def move_right_up_up(self, x):
        return (self.x + x, self.y + x * 2)

    def move_right_up_right(self, x):
        return (self.x + x * 2, self.y + x)

    def move_right_down_right(self, x):
        return (self.x + x * 2, self.y - x)

    def move_right_down_down(self, x):
        return (self.x + x, self.y - x * 2)

    def move_left_down_down(self, x):
        return (self.x - x, self.y - x * 2)

    def move_left_down_left(self, x):
        return (self.x - x * 2, self.y - x)
