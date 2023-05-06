from dataclasses import dataclass, field
from typing import Dict
from pyplanet.apps.core.maniaplanet.models import Player

from .. import Configuration
from ...models.enums.medals import Medals
from ...map_generator import MapGenerator, MapGeneratorType
from ...map_generator.custom import Custom
from ...map_generator.totd import TOTD
from ...models.player_configuration import PlayerConfiguration
from ...games import check_player_allowed_to_change_game_settings
from ...views.player_config_view import PlayerConfigView
from ...views.leaderboard_view import LeaderboardView
from ...views.player_prompt_view import PlayerPromptView

@dataclass
class RandomMapsTogetherConfiguration(Configuration):
    map_generator: MapGenerator
    game_time_seconds: int = field(init=False)
    goal_medal = Medals.AUTHOR
    skip_medal = Medals.GOLD
    enabled = True
    player_configs: Dict[str, PlayerConfiguration] = field(default_factory=dict)
    allow_pausing = False

    def __post_init__(self):
        self.update_player_configs()

    async def update_time_left(self, free_skip=False, goal_medal=False, skip_medal=False):
        pass

    def update_player_configs(self):
        for player in self.app.instance.player_manager.online:
            if not player.login in self.player_configs:
                self.player_configs[player.login] = PlayerConfiguration(
                    player,
                    enabled=True if not self.app.game.game_is_in_progress else self.enabled
                )

    @check_player_allowed_to_change_game_settings
    async def set_game_time_seconds(self, player: Player, buttons):
        time_seconds = await PlayerPromptView.prompt_for_input(
            player, "Game time in seconds", buttons, default=self.game_time_seconds
        )
        self.game_time_seconds = int(time_seconds)
        await self.app.game.views.settings_view.display()


    @check_player_allowed_to_change_game_settings
    async def set_goal_medal(self, _, caller, *_args, **_kwargs):
        self.goal_medal = Medals[caller.split("it_thexivn_RandomMapsTogether_settings__ui_set_goal_medal_")[1].upper()]
        await self.app.game.views.settings_view.display()

    @check_player_allowed_to_change_game_settings
    async def set_skip_medal(self, _, caller, *_args, **_kwargs):
        self.skip_medal = Medals[caller.split("it_thexivn_RandomMapsTogether_settings__ui_set_skip_medal_")[1].upper()]
        await self.app.game.views.settings_view.display()

    @check_player_allowed_to_change_game_settings
    async def toggle_allow_pausing(self, *_args, **_kwargs):
        self.allow_pausing ^= True
        await self.app.game.views.settings_view.display()

    @check_player_allowed_to_change_game_settings
    async def set_map_generator(self, player, caller, *_args, **_kwargs):
        map_generator_string = caller.split("it_thexivn_RandomMapsTogether_settings__ui_set_map_generator_")[1]
        if map_generator_string == "random" and self.map_generator.map_generator_type != MapGeneratorType.RANDOM:
            self.map_generator = MapGenerator(self.app)
            await self.app.map_handler.pre_load_next_map()
        elif map_generator_string == "totd" and self.map_generator.map_generator_type != MapGeneratorType.TOTD:
            self.map_generator = TOTD(self.app)
            await self.app.map_handler.pre_load_next_map()
        elif map_generator_string == "map_pack":
            if self.map_generator.map_generator_type != MapGeneratorType.CUSTOM:
                self.map_generator = Custom(self.app)
            await self.map_generator.maps_ui.display(player) # type: ignore[attr-defined] # pylint: disable=no-member

        await self.app.game.views.settings_view.display()

    async def display_player_settings(self, player, *_args, **_kwargs):
        self.update_player_configs()
        await PlayerConfigView(self.app).display(player)

    async def display_leaderboard(self, player, *_args, **_kwargs):
        await LeaderboardView(self.app).display(player)

    @check_player_allowed_to_change_game_settings
    async def toggle_enabled_players(self, *_args, **_kwargs):
        self.enabled ^= True
        await self.app.game.views.settings_view.display()
