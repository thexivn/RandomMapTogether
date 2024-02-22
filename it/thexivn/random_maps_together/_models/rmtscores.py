from peewee import *
from pyplanet.core.db import TimedModel
from pyplanet.apps.core.maniaplanet.models import Player


class RmtScores(TimedModel):
    score = IntegerField(default=0)

    class Meta:
        db_table = 'rmt_scores'


class AtScores(TimedModel):
    player = ForeignKeyField(Player, index=True)
    at_score = IntegerField(default=0)

    class Meta:
        db_table = 'rmt_at_scores'
