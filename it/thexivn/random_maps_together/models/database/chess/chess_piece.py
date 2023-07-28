from peewee import CharField, IntegerField, ForeignKeyField
from pyplanet.core.db import TimedModel

from .chess_score import ChessScore

class ChessPiece(TimedModel):
    game_score = ForeignKeyField(ChessScore)
    team: CharField(max_length=4)
    type: CharField(max_length=20)
    x: CharField(max_length=1)
    y: IntegerField()

    class Meta:
        indexes = (
            (("game_score"), True),
        )
