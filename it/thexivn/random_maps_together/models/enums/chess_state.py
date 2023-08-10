from enum import Enum


class ChessState(Enum):
    IN_PROGRESS = "In Progress"
    KING_IS_DEAD = "King is dead"
    STALEMATE = "Stalemate"
    CHECKMATE = "Checkmate"
