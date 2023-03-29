from dataclasses import dataclass
import time as py_time

from .Medals import Medals
from .GameModes import GameModes
from ..map_generator import MapGenerators

@dataclass
class Configurations:
    goal_medal = Medals.AUTHOR
    skip_medal = Medals.GOLD
    min_level_to_start = 1
    map_generator = MapGenerators.RANDOM

    def set_min_level_to_start(self, old_value: str, value: str):
        level = int(value)
        if level < 0:
            level = 0
        elif level > 3:
            level = 3

        self.min_level_to_start = level

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        pass

@dataclass
class RMCConfig(Configurations):
    game_mode = GameModes.RANDOM_MAP_CHALLENGE
    game_time_seconds = 3600
    infinite_free_skips = False

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        rmt_game._time_left -= int(py_time.time() - rmt_game._map_start_time)
        rmt_game._scoreboard_ui.set_time_left(rmt_game._time_left)

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

    def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        if free_skip:
            if rmt_game._map_handler.pre_patch_ice or rmt_game._game_state.free_skip_available:
                pass
            else:
                rmt_game._time_left -= self.skip_penalty_seconds
        elif goal_medal:
            rmt_game._time_left += self.goal_bonus_seconds
        elif skip_medal:
            pass

        rmt_game._time_left -= int(py_time.time() - rmt_game._map_start_time)
        rmt_game._scoreboard_ui.set_time_left(rmt_game._time_left)

    def can_skip_map(self, rmt_game):
        return True
