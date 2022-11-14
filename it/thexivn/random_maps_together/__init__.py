import logging

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.command import Command

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
        self.map_handler = MapHandler(self.instance.map_manager)
        self.widget = None
        self.instance.chat()
        self.rmt_game = RMTGame(self.map_handler, self.instance.chat_manager)

        logger.info("application loaded correctly")

    async def on_init(self):
        await super().on_init()
        await self.rmt_game.on_init()
        tm_callbacks.finish.register(self.rmt_game.on_map_finsh)
        mania_callback.map.map_begin.register(self.rmt_game.map_begin_event)
        mania_callback.map.map_end.register(self.rmt_game.map_end_event)
        await self.instance.command_manager.register(
            Command(command="start_rmt", target=self.rmt_game.command_start_rmt, description="load the game"),
            Command(command="stop_rmt", target=self.rmt_game.command_stop_rmt, description="return to lobby"),
            Command(command="skip_gold", target=self.rmt_game.command_skip_gold, description="return to lobby"),
            Command(command="ref", target=self.ref, description="return to lobby")
        )

        self.widget = RandomMapsTogetherView(self)
        await self.widget.display()
        mania_callback.player.player_connect.register(self.player_connect)
        logger.info("application initialized correctly")

    async def on_start(self):
        await super().on_start()

    async def on_stop(self):
        await super().on_stop()
        tm_callbacks.finish.unregister(self.rmt_game.on_map_finsh)
        mania_callback.map.map_begin.unregister(self.rmt_game.map_begin_event)
        mania_callback.map.map_end.unregister(self.rmt_game.map_end_event)

    async def on_destroy(self):
        await super().on_destroy()

    async def player_connect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        if not is_spectator:
            await self.widget.display(player)

    async def ref(self, player: Player, *args, **kwargs):
        await self.widget.display(player)
