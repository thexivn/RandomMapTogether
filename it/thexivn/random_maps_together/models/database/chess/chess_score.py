from peewee import IntegerField
from typing import Union
from pyplanet.core.db import TimedModel


class ChessScore(TimedModel):
    total_time: Union[int, IntegerField] = IntegerField(default=0)
