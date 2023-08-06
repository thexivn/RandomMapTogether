from peewee import IntegerField, ForeignKeyField
from pyplanet.core.db import TimedModel

from .chess_piece import ChessPiece

class ChessMove(TimedModel):
    chess_piece = ForeignKeyField(ChessPiece)
    from_x = IntegerField()
    from_y = IntegerField()
    to_x = IntegerField()
    to_y = IntegerField()
