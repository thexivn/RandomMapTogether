from dataclasses import dataclass
import logging

from pyplanet.apps.core.maniaplanet.models import Player
from . import Configuration
from ...games import check_player_allowed_to_change_game_settings
from ...views.player_prompt_view import PlayerPromptView

logger = logging.getLogger(__name__)

@dataclass
class RMCConfig(Configuration):
    game_time_seconds = 3600
    infinite_free_skips = False
    allow_pausing = False

    async def update_time_left(self, free_skip=False, goal_medal=False, skip_medal=False):
        self.app.game._time_left -= self.app.game._game_state.map_played_time()
        self.app.game._time_left = max(0, self.app.game._time_left)

    def can_skip_map(self):
        return any([
            self.app.game._game_state.free_skip_available,
            self.app.map_handler.pre_patch_ice,
            self.app.game.config.infinite_free_skips,
        ])

    @check_player_allowed_to_change_game_settings
    async def set_game_time_seconds(self, player: Player, caller, values, **kwargs):
        buttons = [
            {"name": "30m", "value": 1800},
            {"name": "1h", "value": 3600},
            {"name": "2h", "value": 7200}
        ]
        time_seconds = await PlayerPromptView.prompt_for_input(player, "Game time in seconds", buttons, default=self.game_time_seconds)
        self.game_time_seconds = int(time_seconds)

        await self.app.game.views.settings_view.display()
