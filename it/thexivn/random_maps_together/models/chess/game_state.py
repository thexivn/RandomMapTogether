from dataclasses import dataclass, field
from typing import Callable, List, Optional
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
        *(Pawn(Team.WHITE, n, 1) for n in range(8)),
        Rook(Team.WHITE, 0, 0),
        Knight(Team.WHITE, 1, 0),
        Bishop(Team.WHITE, 2, 0),
        Queen(Team.WHITE, 3, 0),
        King(Team.WHITE, 4, 0),
        Bishop(Team.WHITE, 5, 0),
        Knight(Team.WHITE, 6, 0),
        Rook(Team.WHITE, 7, 0),
        *(Pawn(Team.BLACK, n, 6) for n in range(8)),
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
    current_map_completed: bool = True
    current_piece: Optional[Piece] = None
    target_piece: Optional[Piece] = None
    state: ChessState = ChessState.IN_PROGRESS
    last_move: Optional[ChessMove] = None

    @property
    def current_king(self):
        return next(piece for piece in self.current_pieces if isinstance(piece, King))

    @property
    def current_pieces(self):
        return (piece for piece in self.pieces_in_play if piece.team == self.turn)

    @property
    def enemy_pieces(self):
        return (piece for piece in self.pieces_in_play if piece.team != self.turn)

    @property
    def pieces_in_play(self):
        return (piece for piece in self.pieces if piece.captured is False)

    def get_pieces_attacking_current_king(self):
        return self.get_enemy_pieces_attacking_coordinate(self.current_king.x, self.current_king.y)

    def get_enemy_pieces_attacking_coordinate(self, x: int, y: int):
        return (
            piece for piece in self.enemy_pieces
            if (x, y) in self.get_moves_for_piece(piece)
        )

    def get_piece_by_coordinate(self, x, y):
        return next((piece for piece in self.pieces_in_play if (x, y) == (piece.x, piece.y)), None)

    def get_moves_for_piece(self, piece: Piece):
        if not piece:
            self.update_game_state()
            return

        for move in piece.moves():
            for step in range(1, 8):
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

                if isinstance(piece, Pawn) and not self.is_valid_pawn_move(piece, move, x, y):
                    continue

                if isinstance(piece, King) and piece.team == self.turn and not self.is_valid_king_move(piece, move):
                    continue

                # Simulate move so that the king does not get attacked
                if piece.team != self.turn or not self.is_valid_simulated_move(piece, x, y):
                    continue

                yield((x, y))
                # Check if target contains a piece
                if next((p for p in self.pieces_in_play if (x, y) == (p.x, p.y)), None):
                    break

    def update_game_state(self):
        current_team_can_move = any((
            any(self.get_moves_for_piece(piece))
            for piece in self.current_pieces
        ))

        pieces_are_attacking_king = any(self.get_pieces_attacking_current_king())
        if not current_team_can_move and pieces_are_attacking_king:
            self.state = ChessState.CHECKMATE
        elif not current_team_can_move and not pieces_are_attacking_king:
            self.state = ChessState.STALEMATE

    def is_valid_pawn_move(self, piece: Pawn, move: Callable, x: int, y: int):
            # Check if there is an enemy piece where pawn could attack
        if move.__name__ in ("move_left_forward", "move_right_forward") \
            and not self.get_piece_by_coordinate(x, y):
            if move.__name__ == "move_left_forward":
                en_passant_piece = self.get_piece_by_coordinate(piece.x-1, piece.y)
            elif move.__name__ == "move_right_forward":
                en_passant_piece = self.get_piece_by_coordinate(piece.x+1, piece.y)

            if not isinstance(en_passant_piece, Pawn):
                return False

            if en_passant_piece.team == piece.team:
                return False

            if not en_passant_piece.last_move or not self.last_move:
                return False

            if en_passant_piece.last_move != self.last_move:
                return False

            if abs(en_passant_piece.last_move.to_y - en_passant_piece.last_move.from_y) != 2:
                return False

        if move.__name__ in ("move_forward", "move_forward_forward") and self.get_piece_by_coordinate(x, y):
            return False

        if move.__name__ == "move_forward_forward" \
            and (self.get_piece_by_coordinate(*piece.move_forward(1)) or piece.last_move):
            return False

        return True

    def is_valid_king_move(self, piece: King, move: Callable):
        if move.__name__ == "castle_left":
            # Check if there are pieces in the way
            if any((self.get_piece_by_coordinate(piece.x - n, piece.y) for n in range(1,4))):
                return False

            rook = self.get_piece_by_coordinate(piece.x - 4, piece.y)
            if not isinstance(rook, Rook):
                return False

            if any((piece.last_move, rook.last_move)):
                return False

            # Check if pieces are attacking king or the steps between
            if any((
                any(self.get_enemy_pieces_attacking_coordinate(piece.x - n, piece.y))
                for n in range(3)
            )):
                return False

        elif move.__name__ == "castle_right":
            # Check if there are pieces in the way
            if any((self.get_piece_by_coordinate(piece.x + n, piece.y) for n in range(1,3))):
                return False

            rook = self.get_piece_by_coordinate(piece.x + 3, piece.y)
            if not isinstance(rook, Rook):
                return False

            if any((piece.last_move, rook.last_move)):
                return False

            # Check if pieces are attacking king or the steps between
            if any((
                any(self.get_enemy_pieces_attacking_coordinate(piece.x + n, piece.y))
                for n in range(3)
            )):
                return False

        return True

    def is_valid_simulated_move(self, piece, x, y):
        # If two pieces are checking the king, the king must move
        if len(list(self.get_pieces_attacking_current_king())) > 1 and not isinstance(piece, King):
            return False

        old_x, old_y = piece.x, piece.y
        target_piece = self.get_piece_by_coordinate(x, y)
        if target_piece:
            target_piece.captured = True
        piece.x, piece.y = x, y

        pieces_attacking_king = any(self.get_pieces_attacking_current_king())

        if target_piece:
            target_piece.captured = False
        piece.x, piece.y = old_x, old_y

        if pieces_attacking_king:
            return False

        return True
