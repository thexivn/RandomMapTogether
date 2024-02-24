import logging
from dataclasses import dataclass, field
from typing import Dict, List

from pyplanet.apps.core.maniaplanet.models import Player


@dataclass
class PlayerScoreInfo:
    player: Player
    player_AT: int = 0


@dataclass
class GameScore:
    total_at: int = 0
    total_gold: int = 0
    player_finishes: Dict[str, PlayerScoreInfo] = field(default_factory=dict)

    def inc_at(self, player: Player):
        self.total_at += 1

        key = player.login
        if key in self.player_finishes:
            self.player_finishes[key].player_AT += 1
        else:
            self.player_finishes[key] = PlayerScoreInfo(player, player_AT=1)

    def inc_gold(self):
        self.total_gold += 1

    def get_top(self, amount=10) -> List[PlayerScoreInfo]:
        if self.player_finishes and len(self.player_finishes) >= 1:
            finishes_scores = [key_val[1] for key_val in self.player_finishes.items()]
            finishes_scores.sort(key=lambda player_score: -player_score.player_AT)
            return finishes_scores[:min(len(self.player_finishes), amount)]

        return []

    def rest(self):
        self.total_gold = 0
        self.total_at = 0
        del self.player_finishes
        self.player_finishes = {}
