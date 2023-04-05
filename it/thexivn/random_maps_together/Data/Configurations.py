from dataclasses import dataclass
import time as py_time
from typing import Dict

from .Medals import Medals
from .GameModes import GameModes
from ..map_generator import MapGenerator
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.config import AppConfig

@dataclass
class PlayerConfig:
    player: Player
    goal_medal: Medals = None
    skip_medal: Medals = None
    enabled: bool = None

@dataclass
class Configurations:
    app: AppConfig
    goal_medal = Medals.AUTHOR
    skip_medal = Medals.GOLD
    enabled = True
    min_level_to_start = 1
    map_generator = None
    player_configs: Dict[str, PlayerConfig] = None

    def __post_init__(self):
        self.map_generator = MapGenerator(self.app)
        self.update_player_configs()

    def set_min_level_to_start(self, old_value: str, value: str):
        level = int(value)
        if level < 0:
            level = 0
        elif level > 3:
            level = 3

        self.min_level_to_start = level

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        pass

    def update_player_configs(self):
        if not self.player_configs:
            self.player_configs = {
                player.login: PlayerConfig(player)
                for player in self.app.instance.player_manager.online
            }
        else:
            for player in self.app.instance.player_manager.online:
                if not player.login in self.player_configs:
                    self.player_configs[player.login] = PlayerConfig(player)

@dataclass
class RMCConfig(Configurations):
    game_mode = GameModes.RANDOM_MAP_CHALLENGE
    game_time_seconds = 3600
    infinite_free_skips = False
    allow_pausing = False

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        rmt_game._time_left -= int(py_time.time() - rmt_game._game_state.map_start_time)

    def can_skip_map(self, rmt_game):
        return any([
            rmt_game._game_state.free_skip_available,
            rmt_game._map_handler.pre_patch_ice,
            rmt_game.app.app_settings.infinite_free_skips,
        ])

@dataclass
class RMSConfig(Configurations):
    game_mode = GameModes.RANDOM_MAP_SURVIVAL
    game_time_seconds = 900
    goal_bonus_seconds = 180
    skip_penalty_seconds = 60
    allow_pausing = False
    total_time_gained = 0

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        if free_skip:
            if rmt_game._map_handler.pre_patch_ice or rmt_game._game_state.free_skip_available:
                pass
            else:
                rmt_game._time_left -= self.skip_penalty_seconds
                self.total_time_gained -= self.skip_penalty_seconds
        elif goal_medal:
            rmt_game._time_left += self.goal_bonus_seconds
            self.total_time_gained += self.goal_bonus_seconds
        elif skip_medal:
            pass

        rmt_game._time_left -= int(py_time.time() - rmt_game._game_state.map_start_time)

    def can_skip_map(self, rmt_game):
        return True
