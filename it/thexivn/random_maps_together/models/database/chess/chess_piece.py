from peewee import CharField, IntegerField, ForeignKeyField, BooleanField
from pyplanet.core.db import TimedModel
from typing import Union

from .chess_score import ChessScore

class ChessPiece(TimedModel):
    game_score: Union[ForeignKeyField, int] = ForeignKeyField(ChessScore)
    team: Union[CharField, str] = CharField(max_length=5)
    piece: Union[CharField, str] = CharField(max_length=20)
    captured: Union[BooleanField, bool] = BooleanField(default=False)
    x: Union[IntegerField, int] = IntegerField()
    y: Union[IntegerField, int] = IntegerField()
