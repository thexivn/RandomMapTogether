from dataclasses import dataclass, field
from typing import Dict, List

from pyplanet.apps.core.maniaplanet.models import Player


@dataclass
class PlayerScoreInfo:
    player: Player
    player_goal_medals: int = 0
    player_skip_medals: int = 0


@dataclass
class GameScore:
    total_goal_medals: int = 0
    total_skip_medals: int = 0
    player_finishes: Dict[str, PlayerScoreInfo] = field(default_factory=dict)

    def inc_goal_medal_count(self, player: Player):
        self.total_goal_medals += 1

        if player.login in self.player_finishes:
            self.player_finishes[player.login].player_goal_medals += 1
        else:
            self.player_finishes[player.login] = PlayerScoreInfo(player, player_goal_medals=1)

    def inc_skip_medal_count(self, player: Player):
        self.total_skip_medals += 1

        if player.login in self.player_finishes:
            self.player_finishes[player.login].player_skip_medals += 1
        else:
            self.player_finishes[player.login] = PlayerScoreInfo(player, player_skip_medals=1)

    def get_top_10(self) -> List[PlayerScoreInfo]:
        return sorted(self.player_finishes.values(), key=lambda player_score: (player_score.player_goal_medals, player_score.player_skip_medals), reverse=True)[:min(len(self.player_finishes), 10)]

    def rest(self):
        self.total_skip_medals = 0
        self.total_goal_medals = 0
        del self.player_finishes
        self.player_finishes = {}
