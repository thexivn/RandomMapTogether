from peewee import CharField, IntegerField
from typing import Union
from pyplanet.core.db import TimedModel


class ChessScore(TimedModel):
    goal_medal = CharField(max_length=7)
    total_time: Union[int, IntegerField] = IntegerField(default=0)
