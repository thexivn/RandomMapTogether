from dataclasses import dataclass
from typing import List

from ..chess.piece import Piece

@dataclass
class GameState:
    pieces: List[Piece]
    current_map_completed: bool = True
