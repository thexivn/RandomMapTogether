from dataclasses import dataclass, field
from typing import Dict, List

from pyplanet.apps.core.maniaplanet.models import Player, Map


@dataclass
class PlayerScoreInfo:
    player: Player
    player_goal_medals: int = 0
    player_skip_medals: int = 0
    goals_on_maps = set()
    skip_medals_on_maps = set()

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

    def rest(self):
        self.total_skip_medals = 0
        self.total_goal_medals = 0
        del self.player_finishes
        self.player_finishes = {}
