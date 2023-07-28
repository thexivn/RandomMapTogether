from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.config import AppConfig

from ..map_generator import MapGenerator, MapGeneratorType
from ..map_generator.custom import Custom
from ..map_generator.totd import TOTD
from ..views.rmt.leaderboard_view import LeaderboardView
from ..settings import MIN_PLAYER_LEVEL_SETTINGS
from ..games import Game

if TYPE_CHECKING:
    from .. import RandomMapsTogetherApp

def check_player_allowed_to_manage_running_game(f):
    async def wrapper(self, player: Player, *args, **kwargs) -> bool:
        if isinstance(self, AppConfig):
            if not(player.level == Player.LEVEL_MASTER or player == self.game.game_starting_player):
                return await self.chat("You are not allowed manage running game", player)
        elif isinstance(self, (Game, Configuration)):
            if not(player.level == Player.LEVEL_MASTER or player == self.app.game.game_starting_player):
                return await self.app.chat("You are not allowed manage running game", player)

        return await f(self, player, *args, **kwargs)
    return wrapper

def check_player_allowed_to_change_game_settings(f):
    async def wrapper(self, player: Player, *args, **kwargs) -> bool:
        if isinstance(self, AppConfig):
            if player.level < await MIN_PLAYER_LEVEL_SETTINGS.get_value():
                return await self.chat("You are not allowed to change game settings", player)
        else:
            if player.level < await MIN_PLAYER_LEVEL_SETTINGS.get_value():
                return await self.app.chat("You are not allowed to change game settings", player)
        return await f(self, player, *args, **kwargs)
    return wrapper

@dataclass
class Configuration:
    app: "RandomMapsTogetherApp"

    def can_skip_map(self):
        pass

    async def display_leaderboard(self, player, *_args, **_kwargs):
        await LeaderboardView(self.app).display(player)

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
