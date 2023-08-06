from peewee import CharField, IntegerField, ForeignKeyField, BooleanField
from pyplanet.core.db import TimedModel

from .chess_score import ChessScore

class ChessPiece(TimedModel):
    game_score = ForeignKeyField(ChessScore)
    team = CharField(max_length=5)
    piece = CharField(max_length=20)
    captured = BooleanField(default=False)
    x = IntegerField()
    y = IntegerField()
