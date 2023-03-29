from dataclasses import dataclass, field
from typing import Dict, List

from .Medals import Medals

from pyplanet.apps.core.maniaplanet.models import Player


@dataclass
class PlayerScoreInfo:
    player: Player
    author_medals: int = 0
    gold_medals: int = 0
    silver_medals: int = 0
    bronze_medals: int = 0
    goal_medals: int = 0
    skip_medals: int = 0


@dataclass
class GameScore:
    goal_medal = None
    skip_medal = None
    total_goal_medals: int = 0
    total_skip_medals: int = 0
    player_finishes: Dict[str, PlayerScoreInfo] = field(default_factory=dict)

    def inc_medal_count(self, player: Player, medal: Medals):
        if not player.login in self.player_finishes:
            self.player_finishes[player.login] = PlayerScoreInfo(player)

        if medal >= self.goal_medal:
            self.total_goal_medals += 1
            self.player_finishes[player.login].goal_medals += 1
        elif medal >= self.skip_medal:
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

    def get_top_10(self) -> List[PlayerScoreInfo]:
        return sorted(self.player_finishes.values(), key=lambda player_score: (player_score.goal_medals, player_score.skip_medals), reverse=True)[:min(len(self.player_finishes), 10)]

    def rest(self):
        self.total_skip_medals = 0
        self.total_goal_medals = 0
        del self.player_finishes
        self.player_finishes = {}
