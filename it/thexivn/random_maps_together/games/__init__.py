import logging

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.config import AppConfig
from ..configuration import Configuration

logger = logging.getLogger(__name__)

def check_player_allowed_to_manage_running_game(f):
    async def wrapper(self, player: Player, *args, **kwargs) -> bool:
        if isinstance(self, AppConfig):
            if not(player.level == Player.LEVEL_MASTER or player == self.game.game_starting_player):
                return await self.chat("You are not allowed manage running game", player)
        elif isinstance(self, Game) or isinstance(self, Configuration):
            if not(player.level == Player.LEVEL_MASTER or player == self.game_starting_player):
                return await self.app.chat("You are not allowed manage running game", player)

        return await f(self, player, *args, **kwargs)
    return wrapper

def check_player_allowed_to_change_game_settings(f):
    async def wrapper(self, player: Player, *args, **kwargs) -> bool:
        if isinstance(self, AppConfig):
            if player.level < self._min_level_to_start:
                return await self.chat("You are not allowed to change game settings", player)
        elif isinstance(self, Game) or isinstance(self, Configuration):
            if player.level < self.app._min_level_to_start:
                return await self.app.chat("You are not allowed to change game settings", player)
        return await f(self, player, *args, **kwargs)
    return wrapper

class Game:
    def __init__(self, app):
        self.app = app
        self.game_starting_player: Player = None
        self.game_is_in_progress = False
        self.views = None

    async def player_connect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        pass

    async def player_disconnect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        pass
