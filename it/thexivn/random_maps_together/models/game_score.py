from dataclasses import dataclass, field
from typing import Dict, List
from pyplanet.apps.core.maniaplanet.models import Player

from .enums.medals import Medals
from .player_score import PlayerScore

@dataclass
class GameScore:
    total_goal_medals: int = 0
    total_skip_medals: int = 0
    player_finishes: Dict[str, PlayerScore] = field(default_factory=dict)

    async def inc_medal_count(self, player: Player, medal: Medals, goal_medal=False, skip_medal=False):
        if not player.login in self.player_finishes:
            self.player_finishes[player.login] = PlayerScore(player)

        if goal_medal:
            self.total_goal_medals += 1
            self.player_finishes[player.login].goal_medals += 1
        elif skip_medal:
            self.total_skip_medals += 1
            self.player_finishes[player.login].skip_medals += 1

        if medal == Medals.AUTHOR:
            self.player_finishes[player.login].author_medals += 1
        elif medal == Medals.GOLD:
            self.player_finishes[player.login].gold_medals += 1
        elif medal == Medals.SILVER:
            self.player_finishes[player.login].silver_medals += 1
        elif medal == Medals.BRONZE:
            self.player_finishes[player.login].bronze_medals += 1

    def get_top_10(self, max_length=10) -> List[PlayerScore]:
        return sorted(self.player_finishes.values(), key=lambda player_score: (player_score.goal_medals, player_score.skip_medals), reverse=True)[:min(len(self.player_finishes), max_length)]

    def rest(self):
        self.total_skip_medals = 0
        self.total_goal_medals = 0
        del self.player_finishes
        self.player_finishes = {}
