from dataclasses import dataclass
from pyplanet.apps.core.maniaplanet.models import Player
from . import RandomMapsTogetherConfiguration
from ...games import check_player_allowed_to_change_game_settings
from ...views.player_prompt_view import PlayerPromptView

@dataclass
class RandomMapSurvivalConfiguration(RandomMapsTogetherConfiguration):
    game_time_seconds = 900
    goal_bonus_seconds = 180
    skip_penalty_seconds = 60

    async def update_time_left(self, free_skip=False, goal_medal=False, skip_medal=False):
        self.app.game.game_state.time_left -= self.app.game.game_state.round_timer.last_round
        if free_skip:
            if self.app.map_handler.pre_patch_ice:
                pass
            else:
                self.game_time_seconds = max(self.game_time_seconds - self.skip_penalty_seconds, 0)
            self.app.game.game_state.time_left = min(self.game_time_seconds, self.app.game.game_state.time_left)

        elif goal_medal:
            self.app.game.game_state.time_left = min(self.app.game.game_state.time_left + self.goal_bonus_seconds, self.game_time_seconds)
        elif skip_medal:
            pass
        self.app.game.game_state.time_left = max(0, self.app.game.game_state.time_left)

    def can_skip_map(self):
        return True

    @check_player_allowed_to_change_game_settings
    async def set_game_time_seconds(self, player: Player, *_args, **_kwargs): # pylint: disable=arguments-differ
        buttons = [
            {"name": "15m", "value": 900},
            {"name": "30m", "value": 1800},
            {"name": "1h", "value": 3600}
        ]
        await super().set_game_time_seconds(player, buttons)

    @check_player_allowed_to_change_game_settings
    async def set_goal_bonus_seconds(self, player: Player, *_args, **_kwargs):
        buttons = [
            {"name": "1m", "value": 60},
            {"name": "3m", "value": 180},
            {"name": "5m", "value": 300}
        ]
        time_seconds = await PlayerPromptView.prompt_for_input(
            player, "Goal bonus in seconds", buttons, default=self.goal_bonus_seconds
        )
        self.goal_bonus_seconds = int(time_seconds)
        await self.app.game.views.settings_view.display()

    @check_player_allowed_to_change_game_settings
    async def set_skip_penalty_seconds(self, player: Player, *_args, **_kwargs):
        buttons = [
            {"name": "30s", "value": 30},
            {"name": "1m", "value": 60},
            {"name": "2m", "value": 120}
        ]
        time_seconds = await PlayerPromptView.prompt_for_input(
            player, "Skip penalty in seconds", buttons, default=self.skip_penalty_seconds
        )
        self.skip_penalty_seconds = int(time_seconds)
        await self.app.game.views.settings_view.display()
