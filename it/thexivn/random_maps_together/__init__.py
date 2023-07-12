import asyncio
import logging
from typing import Dict

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.chat import ChatManager
from pyplanet.contrib.mode import ModeManager
from pyplanet.core.ui import GlobalUIManager
from pyplanet.core.db.database import Database

from .map_handler import MapHandler
from .client.tm_exchange_client import TMExchangeClient
from .views.game_selector_view import GameSelectorView
from .games import Game, check_player_allowed_to_change_game_settings, \
    check_player_allowed_to_manage_running_game
from .games.rmt.random_map_challenge_game import RandomMapChallengeGame
from .constants import S_TIME_LIMIT
from .settings import MIN_PLAYER_LEVEL_SETTINGS

logger = logging.getLogger(__name__)

# TODO: Voting for skip

class RandomMapsTogetherApp(AppConfig):
    app_dependencies = ['core.maniaplanet', 'core.trackmania']
    game_dependencies = ['trackmania_next', 'trackmania']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game: RandomMapChallengeGame
        self.mode_settings: Dict
        self.tmx_client: TMExchangeClient = TMExchangeClient()
        self.map_handler = MapHandler(self, self.instance.map_manager, self.instance.storage)
        self.chat: ChatManager = self.instance.chat
        self.db: Database = self.instance.db
        self.tm_ui_manager: GlobalUIManager = self.instance.ui_manager
        self.mode_manager: ModeManager = self.instance.mode_manager
        self.game_selector = GameSelectorView(self)
        self._min_level_to_start = None

        logger.info("application loaded correctly")

    async def on_init(self):
        await super().on_init()
        self.mode_settings = await self.instance.mode_manager.get_settings()

        self.game = RandomMapChallengeGame(self)
        self.game.config.update_player_configs()
        await self.map_handler.load_hub()
        logger.info("HUB loaded")

        await self.context.setting.register(MIN_PLAYER_LEVEL_SETTINGS)

        await self.game_selector.display()

        mania_callback.player.player_connect.register(self.player_connect)
        mania_callback.player.player_disconnect.register(self.player_disconnect)
        mania_callback.map.map_begin.register(self.map_handler.map_begin_event)

        logger.info("application initialized correctly")

    async def on_start(self):
        await super().on_start()

    async def on_stop(self):
        await super().on_stop()

        mania_callback.player.player_connect.unregister(self.game.player_connect)
        mania_callback.player.player_disconnect.unregister(self.game.player_disconnect)
        mania_callback.map.map_begin.unregister(self.map_handler.map_begin_event)

        await self.game_selector.destroy()

    async def on_destroy(self):
        await super().on_destroy()

    @check_player_allowed_to_change_game_settings
    async def start_game(self, player, *_args, **_kwargs):
        await self.game_selector.hide()
        self.game.game_starting_player = player
        self.game.game_is_in_progress = True

        await self.chat(f'{player.nickname} started new game: {self.game.game_mode.value}')
        try:
            async with self.game as game:
                while game.game_is_in_progress:
                    await asyncio.sleep(1)
        except Exception as e: # pylint: disable=broad-exception-caught
            await self.chat(str(e))
            logger.error("", exc_info=e)

        await self.chat(f"{self.game.game_mode.value} ended")
        await self.map_handler.load_hub()

        self.mode_settings[S_TIME_LIMIT] = 0
        await self.mode_manager.update_settings(self.mode_settings)

        self.game.game_starting_player = None
        await self.game_selector.display()

    @check_player_allowed_to_manage_running_game
    async def stop_game(self, player, *_args, **_kwargs):
        await self.chat(f'{player.nickname} stopped the current game')
        self.game.game_is_in_progress = False

    async def player_connect(self, player: Player, _is_spectator: bool, _source, *_args, **_kwargs):
        if not self.game.game_is_in_progress:
            await self.game_selector.display(player)

    async def player_disconnect(self, _player: Player, _reason: str, _source, *_args, **_kwargs):
        pass
