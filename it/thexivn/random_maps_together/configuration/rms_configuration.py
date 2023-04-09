from dataclasses import dataclass
from . import Configuration
from ..models.enums.game_modes import GameModes

@dataclass
class RMSConfig(Configuration):
    game_mode = GameModes.RANDOM_MAP_SURVIVAL
    game_time_seconds = 900
    goal_bonus_seconds = 180
    skip_penalty_seconds = 60
    allow_pausing = False

    async def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        if free_skip:
            if rmt_game._map_handler.pre_patch_ice or rmt_game._game_state.free_skip_available:
                pass
            else:
                rmt_game._time_left -= self.skip_penalty_seconds
                rmt_game._game_state.total_time_gained -= self.skip_penalty_seconds
        elif goal_medal:
            rmt_game._time_left += self.goal_bonus_seconds
            rmt_game._game_state.total_time_gained += self.goal_bonus_seconds
        elif skip_medal:
            pass
        rmt_game._time_left -= rmt_game._game_state.map_played_time()

    def can_skip_map(self, rmt_game):
        return True
