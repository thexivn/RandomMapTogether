from dataclasses import dataclass
import logging

from pyplanet.apps.core.maniaplanet.models import Player
from . import RandomMapsTogetherConfiguration
from ...games import check_player_allowed_to_change_game_settings

logger = logging.getLogger(__name__)

@dataclass
class RandomMapChallengeConfiguration(RandomMapsTogetherConfiguration):
    game_time_seconds = 3600
    infinite_free_skips = False

    async def update_time_left(self, free_skip=False, goal_medal=False, skip_medal=False):
        self.app.game.game_state.time_left -= self.app.game.game_state.round_timer.last_round
        self.app.game.game_state.time_left = max(0, self.app.game.game_state.time_left)

    def can_skip_map(self):
        return any([
            self.app.game.game_state.free_skip_available,
            self.app.map_handler.pre_patch_ice,
            self.infinite_free_skips,
        ])

    @check_player_allowed_to_change_game_settings
    async def set_game_time_seconds(self, player: Player, *_args, **_kwargs): # pylint: disable=arguments-differ
        buttons = [
            {"name": "30m", "value": 1800},
            {"name": "1h", "value": 3600},
            {"name": "2h", "value": 7200}
        ]
        await super().set_game_time_seconds(player, buttons)

    @check_player_allowed_to_change_game_settings
    async def toggle_infinite_skips(self, _player: Player, *_args, **_kwargs):
        self.infinite_free_skips ^= True
        await self.app.game.views.settings_view.display()
