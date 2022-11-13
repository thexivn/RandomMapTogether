import logging
from enum import Enum

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.chat import ChatManager

from it.thexivn.random_maps_together import MapHandler

logger = logging.getLogger(__name__)


class RMTGame:
    class GameStatus(Enum):
        HUB = 0,
        RMT = 1

    def __init__(self, map_handler: MapHandler, chat: ChatManager):
        self.game_status = RMTGame.GameStatus.HUB
        self.rmt_starter_player: Player = None
        self.skipable_for_gold: bool = False
        self.number_AT = 0
        self.number_gold = 0
        self.map_handler = map_handler
        self.chat = chat
        logger.info("RMT Game initialized")

    async def on_init(self):
        await self.map_handler.load_hub()
        logger.info("RMT Game loaded")

    async def command_start_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.HUB:
            self.change_game_state()
            await self.chat(f'{player.nickname} started new RMT, loading next map ...')
            self.rmt_starter_player = player
            if await self.load_with_retry():
                logger.info("RMT started")
            else:
                self.change_game_state()
                await self.chat("RMT failed to start")
        else:
            await self.chat("RMT already started", player)

    async def load_with_retry(self, max_retry=3) -> bool:
        retry = 0
        load_succeeded = False
        while not load_succeeded and retry < max_retry:
            retry += 1
            try:
                await self.map_handler.load_next_map()
                load_succeeded = True
            except:
                logger.error("failed to load map...")
                await self.map_handler.remove_loaded_map()
                pass

        return retry < max_retry

    async def command_stop_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.RMT:
            if player == self.rmt_starter_player:
                await self.chat(f'{player.nickname} stopped new RMT')
                await self.back_to_hub()
                self.change_game_state()
            else:
                await self.chat("you can't stop the RMT", player)
        else:
            await self.chat("RMT is not started yet")

    async def back_to_hub(self):
        await self.map_handler.remove_loaded_map()
        await self.map_handler.load_hub()
        self.number_AT = 0
        self.number_gold = 0
        self.skipable_for_gold = False
        self.rmt_starter_player = None

    def change_game_state(self):
        self.game_status = RMTGame.GameStatus.HUB if self.game_status == RMTGame.GameStatus.RMT else RMTGame.GameStatus.RMT

    def map_begin_event(self, map, *args, **kwargs):
        logger.info("MAP Begin")
        if self.game_status == RMTGame.GameStatus.RMT:
            self.timer_continue()
            self.map_handler.event_map = map
            self.skipable_for_gold = False

    def map_end_event(self, map, *args, **kwargs):
        logger.info("MAP end")
        if self.game_status == RMTGame.GameStatus.RMT:
            self.timer_pause()
            self.skipable_for_gold = False

    async def on_map_finsh(self, player: Player, race_time: int, lap_time: int, cps, lap_cps, race_cps, flow,
                           is_end_race: bool, is_end_lap, raw, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.RMT:
            if is_end_race:
                if race_time <= self.map_handler.at_time:
                    await self.chat(f'AT TIME, congratulations to {player.nickname}')
                    if await self.load_with_retry():
                        self.number_AT += 1
                    else:
                        await self.back_to_hub()
                        self.change_game_state()
                elif race_time <= self.map_handler.gold_time:
                    self.skipable_for_gold = True
                    await self.chat(f'GOLD TIME now {player.nickname} can /skip_gold to load next map')

    def timer_pause(self):
        logger.info("TIMER PAUSE")
        return

    def timer_continue(self):
        logger.info("TIMER CONTINUE")
        return

    async def command_skip_gold(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.RMT:
            if self.skipable_for_gold:
                if self.rmt_starter_player == player:
                    await self.chat(f'{player.nickname} decided to GOLD skip')
                    if await self.load_with_retry():
                        self.skipable_for_gold = False
                        self.number_gold += 1
                    else:
                        await self.back_to_hub()
                        self.change_game_state()
            else:
                await self.chat("Gold skip is not available", player)
        else:
            await self.chat("You are not allowed to skip", player)

