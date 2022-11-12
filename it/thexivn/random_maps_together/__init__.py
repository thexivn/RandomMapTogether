import logging
from enum import Enum

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.command import Command

from it.thexivn.random_maps_together.MapHandler import MapHandler
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks


class GameStatus(Enum):
    HUB = 0,
    GAME = 1


class RandomMapsTogetherApp(AppConfig):
    app_dependencies = ['core.maniaplanet', 'core.trackmania']
    game_dependencies = ['trackmania_next', 'trackmania']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.info("it.thexivn.RandomMapsTogether LOADED")
        logging.info(self.instance.storage.driver.base_dir)
        self.map_handler = MapHandler(self.instance.map_manager)
        self.game_status = GameStatus.HUB

        # self.context.signals.listen(tm_callbacks.finish, self.on_map_finsh)

    async def on_init(self):
        await super().on_init()
        await self.map_handler.on_init()
        tm_callbacks.finish.register(self.on_map_finsh)
        await self.instance.command_manager.register(
            Command(command="start_rmt", target=self.start_rmt, description="load the game"),
            Command(command="stop_rmt", target=self.stop_rmt, description="return to lobby"),
            Command(command="skip", target=self.skip, description="return to lobby")
        )

    async def on_start(self):
        await super().on_start()

    async def on_stop(self):
        await super().on_stop()
        tm_callbacks.finish.unregister(self.on_map_finsh)

    async def on_destroy(self):
        await super().on_destroy()

    async def start_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == GameStatus.HUB:
            logging.info("Starting RMT")
            await self.map_handler.load_next_map()
            self.game_status = GameStatus.GAME

    async def stop_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == GameStatus.GAME:
            logging.info("return to lobby")
            await self.map_handler.load_hub()
            self.game_status = GameStatus.HUB

    async def skip(self, player: Player, *args, **kwargs):
        if self.game_status == GameStatus.GAME:
            await self.map_handler.load_next_map()

    async def on_map_finsh(self, player: Player, race_time, lap_time, cps, lap_cps, race_cps, flow, is_end_race, is_end_lap,
                   raw, *args, **kwargs):
        if self.game_status == GameStatus.GAME:
            logging.info("player: %s, done: %d", player.nickname, lap_time)
            if lap_time < self.map_handler.AT:
                await self.map_handler.load_next_map()
