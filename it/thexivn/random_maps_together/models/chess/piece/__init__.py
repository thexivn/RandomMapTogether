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

    async def get_last_move(self):
        moves =  await ChessMove.execute(
            ChessMove
            .select(ChessMove)
            .where(ChessMove.chess_piece == self.db.id)
            .order_by(ChessMove.id.desc())
            .limit(1)
        )

        return moves[0] if len(moves) else None
