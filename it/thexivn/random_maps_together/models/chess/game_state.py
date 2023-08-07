from dataclasses import dataclass, field
from typing import List, Optional
import logging

from ..enums.team import Team
from ..chess.piece import Piece
from ..chess.piece.bishop import Bishop
from ..chess.piece.king import King
from ..chess.piece.knight import Knight
from ..chess.piece.pawn import Pawn
from ..chess.piece.queen import Queen
from ..chess.piece.rook import Rook
from ..database.chess.chess_move import ChessMove

logger = logging.getLogger(__name__)

def create_default_pieces():
    return [
        Pawn(Team.WHITE, 0, 1),
        Pawn(Team.WHITE, 1, 1),
        Pawn(Team.WHITE, 2, 1),
        Pawn(Team.WHITE, 3, 1),
        Pawn(Team.WHITE, 4, 1),
        Pawn(Team.WHITE, 5, 1),
        Pawn(Team.WHITE, 6, 1),
        Pawn(Team.WHITE, 7, 1),
        Rook(Team.WHITE, 0, 0),
        Knight(Team.WHITE, 1, 0),
        Bishop(Team.WHITE, 2, 0),
        Queen(Team.WHITE, 3, 0),
        King(Team.WHITE, 4, 0),
        Bishop(Team.WHITE, 5, 0),
        Knight(Team.WHITE, 6, 0),
        Rook(Team.WHITE, 7, 0),
        Pawn(Team.BLACK, 0, 6),
        Pawn(Team.BLACK, 1, 6),
        Pawn(Team.BLACK, 2, 6),
        Pawn(Team.BLACK, 3, 6),
        Pawn(Team.BLACK, 4, 6),
        Pawn(Team.BLACK, 5, 6),
        Pawn(Team.BLACK, 6, 6),
        Pawn(Team.BLACK, 7, 6),
        Rook(Team.BLACK, 0, 7),
        Knight(Team.BLACK, 1, 7),
        Bishop(Team.BLACK, 2, 7),
        Queen(Team.BLACK, 3, 7),
        King(Team.BLACK, 4, 7),
        Bishop(Team.BLACK, 5, 7),
        Knight(Team.BLACK, 6, 7),
        Rook(Team.BLACK, 7, 7),
    ]

@dataclass
class GameState:
    pieces: List[Piece] = field(default_factory=create_default_pieces)
    turn: Team = Team.WHITE
    current_piece: Optional[Piece] = None

    @property
    def white_pieces(self):
        return [piece for piece in self.pieces if piece.team == Team.WHITE]

    @property
    def white_pieces_in_play(self):
        return [piece for piece in self.pieces if piece.team == Team.WHITE and piece.captured is False]

    @property
    def black_pieces(self):
        return [piece for piece in self.pieces if piece.team == Team.WHITE]

    @property
    def black_pieces_in_play(self):
        return [piece for piece in self.pieces if piece.team == Team.BLACK and piece.captured is False]

    @property
    def pieces_in_play(self):
        return [piece for piece in self.pieces if piece.captured is False]

    async def get_piece_by_coordinate(self, x, y):
        return next((piece for piece in self.pieces_in_play if piece.x == x and piece.y == y), None)

    async def get_moves_for_piece(self, piece: Piece):
        moves = []
        if not piece:
            return moves
        for move in piece.moves():
            for step in range(1, 9):
                x, y = move(step)
                if isinstance(piece, Pawn):
                    if move.__name__ in ("move_left_forward", "move_right_forward") and await self.get_piece_by_coordinate(x, y) is None:
                        if move.__name__ == "move_left_forward":
                            en_passant_piece = await self.get_piece_by_coordinate(piece.x-1, piece.y)
                        elif move.__name__ == "move_right_forward":
                            en_passant_piece = await self.get_piece_by_coordinate(piece.x+1, piece.y)

                        if isinstance(en_passant_piece, Pawn) and en_passant_piece.team != piece.team:
                            last_move = await en_passant_piece.get_last_move()
                            if not last_move:
                                continue

                            last_move_in_game = next((move for move in await ChessMove.execute(ChessMove.select(ChessMove).order_by(ChessMove.id.desc()).limit(1))), None)
                            if not last_move_in_game:
                                continue

                            if last_move_in_game != last_move:
                                continue

                            if abs(last_move.to_y - last_move.from_y) != 2:
                                continue

                        else:
                            continue

                    if move.__name__ in ("move_forward", "move_forward_forward") and await self.get_piece_by_coordinate(x, y):
                        continue

                    if move.__name__ == "move_forward_forward" and (await self.get_piece_by_coordinate(*piece.move_forward(step)) or len(await ChessMove.execute(ChessMove.select(ChessMove).where(ChessMove.chess_piece == piece.db.id)))):
                        continue

                elif isinstance(piece, King) and piece.team == self.turn:
                    if move.__name__ == "castle_left":
                        if any([await self.get_piece_by_coordinate(piece.x - n, y) for n in range(1,4)]):
                            continue

                        rook = await self.get_piece_by_coordinate(piece.x - 4, piece.y)
                        if not rook:
                            continue

                        if rook and any([await piece.get_last_move(), await rook.get_last_move()]):
                            continue

                        if any([
                            move == (piece.x - n, piece.y)
                            for n in range(3)
                            for piece_in_play in (self.black_pieces_in_play if piece.team == Team.WHITE else self.white_pieces_in_play)
                            for move in await self.get_moves_for_piece(piece_in_play)
                        ]):
                            continue

                    elif move.__name__ == "castle_right":
                        if any([await self.get_piece_by_coordinate(piece.x + n, y) for n in range(1,3)]):
                            continue

                        rook = await self.get_piece_by_coordinate(piece.x + 3, piece.y)
                        if not rook:
                            continue

                        if rook and any([await piece.get_last_move(), await rook.get_last_move()]):
                            continue

                        if any([
                            move == (piece.x + n, piece.y)
                            for n in range(3)
                            for piece_in_play in (self.black_pieces_in_play if piece.team == Team.WHITE else self.white_pieces_in_play)
                            for move in await self.get_moves_for_piece(piece_in_play)
                        ]):
                            continue

                if piece.max_steps is not None and step > piece.max_steps:
                    break
                if x not in range(8) or y not in range(8):
                    continue
                if next((p for p in self.pieces_in_play if p.x == x and p.y == y and p.team == piece.team), None):
                    break
                moves.append((x, y))
                if next((p for p in self.pieces_in_play if p.x == x and p.y == y), None):
                    break
        return moves
