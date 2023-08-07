from dataclasses import dataclass
from typing import Tuple

from . import Piece


@dataclass
class King(Piece):
    max_steps: int = 1

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
            self.castle_left,
            self.castle_right,
        ]

    def move_left(self, x: int) -> Tuple[int, int]:
        return (self.x - x, self.y)

    def move_left_up(self, x: int) -> Tuple[int, int]:
        return (self.x - x, self.y + x)

    def move_up(self, x: int) -> Tuple[int, int]:
        return (self.x, self.y + x)

    def move_right_up(self, x: int) -> Tuple[int, int]:
        return (self.x + x, self.y + x)

    def move_right(self, x: int) -> Tuple[int, int]:
        return (self.x + x, self.y)

    def move_right_down(self, x: int) -> Tuple[int, int]:
        return (self.x + x, self.y - x)

    def move_down(self, x: int) -> Tuple[int, int]:
        return (self.x, self.y - x)

    def move_left_down(self, x: int) -> Tuple[int, int]:
        return (self.x - x, self.y - x)

    def castle_left(self, x: int) -> Tuple[int, int]:
        return (self.x - 2 * x, self.y)

    def castle_right(self, x: int) -> Tuple[int, int]:
        return (self.x + 2 * x, self.y)
