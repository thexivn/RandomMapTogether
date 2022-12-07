import logging

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting

from it.thexivn.random_maps_together.Data.Configurations import Configurations
from it.thexivn.random_maps_together.Data.Constants import *
from it.thexivn.random_maps_together.RMTGame import RMTGame
from it.thexivn.random_maps_together.MapHandler import MapHandler
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks

from it.thexivn.random_maps_together.views import RandomMapsTogetherView
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback

logger = logging.getLogger(__name__)


class RandomMapsTogetherApp(AppConfig):
    app_dependencies = ['core.maniaplanet', 'core.trackmania']
    game_dependencies = ['trackmania_next', 'trackmania']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_settings: Configurations = Configurations()
        self.map_handler = MapHandler(self.instance.map_manager, self.instance.storage, self.app_settings)
        self.instance.chat()
        self.widget = RandomMapsTogetherView(self)
        self.rmt_game = RMTGame(self.map_handler, self.instance.chat_manager, self.instance.mode_manager,
                                self.widget, self.app_settings, self.instance.ui_manager)

        logger.info("application loaded correctly")

    async def on_init(self):
        await super().on_init()

        await self.rmt_game.on_init()
        tm_callbacks.finish.register(self.rmt_game.on_map_finsh)
        mania_callback.map.map_begin.register(self.rmt_game.map_begin_event)
        mania_callback.flow.round_end.register(self.rmt_game.map_end_event)
        mania_callback.flow.match_end__end.register(self.rmt_game.hide_custom_scoreboard)
        mania_callback.flow.round_start__end.register(self.rmt_game.set_time_left)

        await self.instance.command_manager.register(
            Command(command="start_rmt", target=self.rmt_game.command_start_rmt, description="load the game"),
            Command(command="stop_rmt", target=self.rmt_game.command_stop_rmt, description="return to lobby"),
            Command(command="skip_gold", target=self.rmt_game.command_skip_gold,
                    description="skip current map is GOLD time is reached"),
            Command(command="skip", target=self.rmt_game.command_free_skip,
                    description="skip current map once per game"),
        )

        await self.settings()

        mania_callback.player.player_connect.register(self.player_connect)
        logger.info("application initialized correctly")

    async def settings(self):
        game_time: Setting = Setting('it.thexivn.RMT.game_time', 'game_time', Setting.CAT_BEHAVIOUR, int,
                                     'time of the session', default=3600,
                                     change_target=self.app_settings.set_game_time)

        at_time: Setting = Setting('it.thexivn.RMT.AT_time', 'AT_time', Setting.CAT_BEHAVIOUR, str,
                                   'time to complete the map', default=AT, choices=[AT, GOLD, SILVER],
                                   change_target=self.app_settings.set_at_time)

        gold_time: Setting = Setting('it.thexivn.RMT.GOLD_time', 'GOLD_time', Setting.CAT_BEHAVIOUR, str,
                                     'set the time that allow you to skip the map', default=GOLD,
                                     choices=[GOLD, SILVER, BRONZE], change_target=self.app_settings.set_gold_time)

        perm: Setting = Setting('it.thexivn.RMT.min_perm_start', 'min_perm_start', Setting.CAT_BEHAVIOUR, int,
                                'permission level to start the RMT', default=2,
                                change_target=self.app_settings.set_min_level_to_start)

        await self.context.setting.register(
            game_time,
            at_time,
            gold_time,
            perm
        )
        self.app_settings.set_game_time(3600, await game_time.get_value())
        self.app_settings.set_at_time(AT, await at_time.get_value())
        self.app_settings.set_gold_time(GOLD, await gold_time.get_value())
        self.app_settings.set_min_level_to_start(2, await perm.get_value())

    async def on_start(self):
        await super().on_start()

    async def on_stop(self):
        await super().on_stop()
        tm_callbacks.finish.unregister(self.rmt_game.on_map_finsh)
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

    async def ref(self, player: Player, *args, **kwargs):
        await self.widget.display(player)
