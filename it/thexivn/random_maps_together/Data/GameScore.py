from dataclasses import dataclass, field
from typing import Dict, List

from .Medals import Medals

from pyplanet.apps.core.maniaplanet.models import Player


@dataclass
class PlayerScoreInfo:
    player: Player
    player_goal_medals: int = 0
    player_skip_medals: int = 0
    goals_on_maps = set()
    skip_medals_on_maps = set()
    author_medals: int = 0
    gold_medals: int = 0
    silver_medals: int = 0
    bronze_medals: int = 0
    goal_medals: int = 0
    skip_medals: int = 0

    def incr_medal_for(self, uid: str) -> bool:
        if uid in self.goals_on_maps:
            return False
        if uid in self.skip_medals_on_maps:
            self.player_skip_medals -= 1
        self.goals_on_maps.add(uid)
        self.player_goal_medals += 1
        return True

    def incr_skip_medal_for(self, uid: str) -> bool:
        if uid in self.skip_medals_on_maps:
            return False
        self.skip_medals_on_maps.add(uid)
        self.player_skip_medals += 1
        return True



@dataclass
class GameScore:
    goal_medal = None
    skip_medal = None
    total_goal_medals: int = 0
    total_skip_medals: int = 0
    player_finishes: Dict[str, PlayerScoreInfo] = field(default_factory=dict)

    def get_players_score(self, player: Player):
        psi = self.player_finishes.get(player.login, PlayerScoreInfo(player))
        self.player_finishes[player.login] = psi
        return psi

    def inc_goal_medal_count(self, player: Player, map: Map, count_globally: bool) -> bool:
        psi = self.get_players_score(player)
        counted_for_player = psi.incr_medal_for(map.uid)
        if counted_for_player and count_globally:
            self.total_goal_medals += 1
        return counted_for_player

    def inc_skip_medal_count(self, player: Player, map: Map, count_globally: bool) -> bool:
        psi = self.get_players_score(player)
        counted_for_player = psi.incr_skip_medal_for(map.uid)
        if counted_for_player and count_globally:
            self.total_skip_medals += 1
        return counted_for_player

    def get_top_10(self, max_len=10) -> List[PlayerScoreInfo]:
        return sorted(self.player_finishes.values(), key=lambda player_score: (player_score.player_goal_medals, player_score.player_skip_medals), reverse=True)[:min(len(self.player_finishes), max_len)]
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
