from enum import Enum


class ChessState(Enum):
    IN_PROGRESS = "In Progress"
    STALEMATE = "Stalemate"
    CHECKMATE = "Checkmate"
