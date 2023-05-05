from peewee import CharField, IntegerField, ForeignKeyField
from pyplanet.core.db import TimedModel
from pyplanet.apps.core.maniaplanet.models import Player

from .random_maps_together_score import RandomMapsTogetherScore
from ...enums.medals import Medals

class RandomMapsTogetherPlayerScore(TimedModel):
    game_score = ForeignKeyField(RandomMapsTogetherScore)
    player = ForeignKeyField(Player)
    goal_medal = CharField(max_length=7, null=True)
    skip_medal = CharField(max_length=7, null=True)
    author_medals = IntegerField(default=0)
    gold_medals = IntegerField(default=0)
    silver_medals = IntegerField(default=0)
    bronze_medals = IntegerField(default=0)
    total_goal_medals = IntegerField(default=0)
    total_skip_medals = IntegerField(default=0)
    medal_sum = IntegerField(default=0)

    class Meta:
        indexes = (
            (("game_score", "player"), True),
        )

    @staticmethod
    async def get_top_20_players(game_id: int):
        return await RandomMapsTogetherPlayerScore.execute(
            RandomMapsTogetherPlayerScore
            .select(RandomMapsTogetherPlayerScore, Player)
            .join(Player)
            .where(RandomMapsTogetherPlayerScore.game_score == game_id)
            .order_by(
                RandomMapsTogetherPlayerScore.goal_medal,
                RandomMapsTogetherPlayerScore.skip_medal,
                RandomMapsTogetherPlayerScore.total_goal_medals.desc(),
                RandomMapsTogetherPlayerScore.total_skip_medals.desc(),
                RandomMapsTogetherPlayerScore.author_medals.desc(),
                RandomMapsTogetherPlayerScore.gold_medals.desc(),
                RandomMapsTogetherPlayerScore.silver_medals.desc(),
                RandomMapsTogetherPlayerScore.bronze_medals.desc(),
            )
            .limit(20)
        )

    async def increase_medal_count(self, medal: Medals):
        self.medal_sum += medal.value
        if medal == Medals.AUTHOR:
            self.author_medals += 1
        elif medal == Medals.GOLD:
            self.gold_medals += 1
        elif medal == Medals.SILVER:
            self.silver_medals += 1
        elif medal == Medals.BRONZE:
            self.bronze_medals += 1
