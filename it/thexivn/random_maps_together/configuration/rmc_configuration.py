from dataclasses import dataclass

from . import Configuration
from ..models.enums.game_modes import GameModes

@dataclass
class RMCConfig(Configuration):
    game_mode = GameModes.RANDOM_MAP_CHALLENGE
    game_time_seconds = 3600
    infinite_free_skips = False
    allow_pausing = False

    async def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        rmt_game._time_left -= rmt_game._game_state.map_played_time()

    def can_skip_map(self, rmt_game):
        return any([
            rmt_game._game_state.free_skip_available,
            rmt_game._map_handler.pre_patch_ice,
            rmt_game.app.app_settings.infinite_free_skips,
        ])
