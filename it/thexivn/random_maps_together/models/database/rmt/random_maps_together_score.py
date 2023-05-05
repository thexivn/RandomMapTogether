from peewee import BooleanField, CharField, IntegerField
from pyplanet.core.db import TimedModel

class RandomMapsTogetherScore(TimedModel):
    game_mode = CharField(max_length=50)
    goal_medal = CharField(max_length=7)
    skip_medal = CharField(max_length=7)
    total_goal_medals = IntegerField(default=0)
    total_skip_medals = IntegerField(default=0)
    medal_sum = IntegerField(default=0)
    modified_player_settings = BooleanField(default=False)
    game_time_seconds = IntegerField(default=0)
    total_time_gained = IntegerField(default=0)
