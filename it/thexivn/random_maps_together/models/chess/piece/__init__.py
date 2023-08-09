from dataclasses import dataclass
from typing import Optional

from ...enums.team import Team
from ...database.chess.chess_piece import ChessPiece
from ...database.chess.chess_move import ChessMove

@dataclass
class Piece:
    team: Team
    x: int
    y: int
    db: Optional[ChessPiece] = None
    max_steps: Optional[int] = None
    captured: bool = False
    last_move: Optional[ChessMove] = None
