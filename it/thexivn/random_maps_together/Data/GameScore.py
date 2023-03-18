from dataclasses import dataclass, field
from typing import Dict, List

from pyplanet.apps.core.maniaplanet.models import Player


@dataclass
class PlayerScoreInfo:
    player: Player
    player_goal_medals: int = 0


@dataclass
class GameScore:
    total_goal_medals: int = 0
    total_skip_medals: int = 0
    player_finishes: Dict[str, PlayerScoreInfo] = field(default_factory=dict)

    def inc_at(self, player: Player):
        self.total_goal_medals += 1

        key = player.login
        if key in self.player_finishes:
            self.player_finishes[key].player_goal_medals += 1
        else:
            self.player_finishes[key] = PlayerScoreInfo(player, player_goal_medals=1)

    def inc_gold(self):
        self.total_skip_medals += 1

    def get_top_10(self) -> List[PlayerScoreInfo]:
        if self.player_finishes and len(self.player_finishes) >= 1:
            finishes_scores = [key_val[1] for key_val in self.player_finishes.items()]
            finishes_scores.sort(key=lambda player_score: -player_score.player_goal_medals)
            return finishes_scores[:min(len(self.player_finishes), 10)]

        return []

    def rest(self):
        self.total_skip_medals = 0
        self.total_goal_medals = 0
        del self.player_finishes
        self.player_finishes = {}
