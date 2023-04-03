import logging
import requests

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting

from .Data.Configurations import Configurations, RMCConfig
from .RMTGame import RMTGame
from .MapHandler import MapHandler
from .views import RandomMapsTogetherView

logger = logging.getLogger(__name__)


class RandomMapsTogetherApp(AppConfig):
    app_dependencies = ['core.maniaplanet', 'core.trackmania']
    game_dependencies = ['trackmania_next', 'trackmania']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.app_settings: Configurations = RMCConfig(self)
        self.map_handler = MapHandler(self, self.instance.map_manager, self.instance.storage)
        self.instance.chat()
        self.widget = RandomMapsTogetherView(self)
        self.rmt_game = RMTGame(self, self.map_handler, self.instance.chat_manager, self.instance.mode_manager,
                                self.widget, self.instance.ui_manager)

        logger.info("application loaded correctly")

    async def on_init(self):
        await super().on_init()

        await self.rmt_game.on_init()
        tm_callbacks.finish.register(self.rmt_game.on_map_finish)
        mania_callback.map.map_begin.register(self.rmt_game.map_begin_event)
        mania_callback.flow.round_end.register(self.rmt_game.map_end_event)
        mania_callback.flow.match_end__end.register(self.rmt_game.hide_custom_scoreboard)
        mania_callback.flow.round_start__end.register(self.rmt_game.set_time_left)

        await self.instance.command_manager.register(
            Command(command="start_rmt", target=self.rmt_game.command_start_rmt, description="load the game"),
            Command(command="stop_rmt", target=self.rmt_game.command_stop_rmt, description="return to lobby"),
            Command(command="skip_medal", target=self.rmt_game.command_skip_medal,
                    description="skip current map is GOLD time is reached"),
            Command(command="skip", target=self.rmt_game.command_free_skip,
                    description="skip current map once per game"),
        )

        await self.settings()
        await self.instance.gbx.multicall(
            self.instance.gbx.prepare('SetCallVoteRatios', [-1])
        )

        mania_callback.player.player_connect.register(self.player_connect)
        logger.info("application initialized correctly")

    async def settings(self):
        perm: Setting = Setting('it.thexivn.RMT.min_perm_start', 'min_perm_start', Setting.CAT_BEHAVIOUR, int,
                                'permission level to start the RMT', default=2,
                                change_target=self.app_settings.set_min_level_to_start)

        await self.context.setting.register(
            perm
        )
        self.app_settings.set_min_level_to_start(2, await perm.get_value())

    async def on_start(self):
        await super().on_start()

    async def on_stop(self):
        await super().on_stop()
        tm_callbacks.finish.unregister(self.rmt_game.on_map_finish)
        mania_callback.map.map_begin.unregister(self.rmt_game.map_begin_event)
        mania_callback.flow.round_end.unregister(self.rmt_game.map_end_event)
        mania_callback.flow.match_end__end.unregister(self.rmt_game.hide_custom_scoreboard)
        mania_callback.flow.round_start__end.unregister(self.rmt_game.set_time_left)
        await self.widget.destroy()
        self.instance.ui_manager.properties.set_visibility('Race_ScoresTable', True)
        self.instance.ui_manager.properties.set_visibility('Race_BigMessage', True)
        await self.instance.ui_manager.properties.send_properties()

    async def on_destroy(self):
        await super().on_destroy()

    async def player_connect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        if not is_spectator:
            await self.widget.display(player)
            if self.rmt_game._game_state.game_is_in_progress:
                self.app_settings.update_player_configs()

    async def player_disconnect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        if not is_spectator:
            self.app_settings.player_configs.pop(player.login, None)

    async def ref(self, player: Player, *args, **kwargs):
        await self.widget.display(player)
