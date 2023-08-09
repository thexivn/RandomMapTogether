from dataclasses import dataclass, field
from typing import List, Optional
import logging

from ..enums.team import Team
from ..enums.chess_state import ChessState
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
    state: ChessState = ChessState.IN_PROGRESS
    last_move: Optional[ChessMove] = None

    @property
    def current_king(self):
        return next(piece for piece in self.pieces_in_play if piece.team == self.turn and isinstance(piece, King))

    @property
    def current_pieces(self):
        return tuple(piece for piece in self.pieces_in_play if piece.team == self.turn)

    @property
    def enemy_pieces(self):
        return tuple(piece for piece in self.pieces_in_play if piece.team != self.turn)

    @property
    def pieces_in_play(self):
        return tuple(piece for piece in self.pieces if piece.captured is False)

    async def get_pieces_attacking_current_king(self):
        return await self.get_enemy_pieces_attacking_coordinate(self.current_king.x, self.current_king.y)

    async def get_enemy_pieces_attacking_coordinate(self, x: int, y: int):
        return [
            piece for piece in self.enemy_pieces
            for move in await self.get_moves_for_piece(piece)
            if (x, y) == move
        ]

    async def get_piece_by_coordinate(self, x, y):
        return next((piece for piece in self.pieces_in_play if (x, y) == (piece.x, piece.y)), None)

    async def get_moves_for_piece(self, piece: Piece):
        moves = []
        if not piece:
            current_team_can_move = bool([
                move
                for piece in self.current_pieces
                for move in await self.get_moves_for_piece(piece)
            ])
            pieces_attacking_king = await self.get_pieces_attacking_current_king()

            if not current_team_can_move and pieces_attacking_king:
                self.game_state.state = ChessState.CHECKMATE
                self.game_is_in_progress = False
            elif not current_team_can_move and not pieces_attacking_king:
                self.game_state.state = ChessState.STALEMATE
                self.game_is_in_progress = False

            return moves

        for move in piece.moves():
            for step in range(1, 9):
                x, y = move(step)

                # Check if piece has moved max number of steps
                if piece.max_steps is not None and step > piece.max_steps:
                    break
                # Check if move is outside board
                if x not in range(8) or y not in range(8):
                    continue

                # Check if target has friendly piece
                if next((p for p in self.pieces_in_play if (x, y) == (p.x, p.y) and p.team == piece.team), None):
                    break

                if isinstance(piece, Pawn):
                    # Check if there is an enemy piece where pawn could attack
                    if move.__name__ in ("move_left_forward", "move_right_forward") and await self.get_piece_by_coordinate(x, y) is None:
                        if move.__name__ == "move_left_forward":
                            en_passant_piece = await self.get_piece_by_coordinate(piece.x-1, piece.y)
                        elif move.__name__ == "move_right_forward":
                            en_passant_piece = await self.get_piece_by_coordinate(piece.x+1, piece.y)

                        if isinstance(en_passant_piece, Pawn) and en_passant_piece.team != piece.team:
                            if not en_passant_piece.last_move or not self.last_move:
                                continue

                            if en_passant_piece.last_move != self.last_move:
                                continue

                            if abs(en_passant_piece.last_move.to_y - en_passant_piece.last_move.from_y) != 2:
                                continue

                        else:
                            continue

                    if move.__name__ in ("move_forward", "move_forward_forward") and await self.get_piece_by_coordinate(x, y):
                        continue

                    if move.__name__ == "move_forward_forward" and (await self.get_piece_by_coordinate(*piece.move_forward(step)) or piece.last_move):
                        continue

                elif isinstance(piece, King) and piece.team == self.turn:
                    if move.__name__ == "castle_left":
                        # Check if there are pieces in the way
                        if any([await self.get_piece_by_coordinate(piece.x - n, y) for n in range(1,4)]):
                            continue

                        rook = await self.get_piece_by_coordinate(piece.x - 4, piece.y)
                        if not rook:
                            continue

                        if rook and any([piece.last_move, rook.last_move]):
                            continue

                        # Check if pieces are attacking king or the steps between
                        if any([
                            await self.get_enemy_pieces_attacking_coordinate(piece.x - n, piece.y)
                            for n in range(3)
                        ]):
                            continue

                    elif move.__name__ == "castle_right":
                        # Check if there are pieces in the way
                        if any([await self.get_piece_by_coordinate(piece.x + n, y) for n in range(1,3)]):
                            continue

                        rook = await self.get_piece_by_coordinate(piece.x + 3, piece.y)
                        if not rook:
                            continue

                        if rook and any([piece.last_move, rook.last_move]):
                            continue

                        # Check if pieces are attacking king or the steps between
                        if any([
                            await self.get_enemy_pieces_attacking_coordinate(piece.x + n, piece.y)
                            for n in range(3)
                        ]):
                            continue

                # Simulate move so that the king does not get attacked
                if piece.team == self.turn:
                    pieces_attacking_king = await self.get_pieces_attacking_current_king()
                    # If two pieces are checking the king, the king must move
                    if len(pieces_attacking_king) > 1 and not isinstance(piece, King):
                        continue

                    old_x, old_y = piece.x, piece.y
                    target_piece = await self.get_piece_by_coordinate(x, y)
                    if target_piece:
                        target_piece.captured = True
                    piece.x, piece.y = x, y

                    pieces_attacking_king = await self.get_pieces_attacking_current_king()

                    if target_piece:
                        target_piece.captured = False
                    piece.x, piece.y = old_x, old_y

                    if pieces_attacking_king:
                        continue

                moves.append((x, y))
                # Check if target contains a piece
                if next((p for p in self.pieces_in_play if (x, y) == (p.x, p.y)), None):
                    break
        return moves
