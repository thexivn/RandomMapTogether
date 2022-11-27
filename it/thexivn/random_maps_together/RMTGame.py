import asyncio
import logging
import time as py_time
from enum import Enum

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.chat import ChatManager
from pyplanet.contrib.mode import ModeManager

from it.thexivn.random_maps_together import MapHandler
from it.thexivn.random_maps_together.Data.Configurations import Configurations
from it.thexivn.random_maps_together.Data.GameScore import GameScore

from it.thexivn.random_maps_together.views import RandomMapsTogetherView

S_TIME_LIMIT = 'S_TimeLimit'
_lock = asyncio.Lock()

logger = logging.getLogger(__name__)


class RMTGame:
    class GameStatus(Enum):
        HUB = 0,
        RMT = 1

    def __init__(self, map_handler: MapHandler, chat: ChatManager, mode_manager: ModeManager,
                 score_ui: RandomMapsTogetherView, config: Configurations):
        self.game_status = RMTGame.GameStatus.HUB
        self.rmt_starter_player: Player = None
        self.skipable_for_gold: bool = False
        self._score = GameScore()
        self.map_handler = map_handler
        self.chat = chat
        self.mode_manager = mode_manager
        self._mode_settings = None
        self._map_start_time = py_time.time()
        self._config = config
        self._time_left = config.game_time_seconds
        self.score_ui = score_ui
        self.score_ui.set_score(self._score)
        self._map_completed = True
        logger.info("RMT Game initialized")

    async def on_init(self):
        await self.map_handler.load_hub()
        logger.info("RMT Game loaded")
        self._mode_settings = await self.mode_manager.get_settings()
        await self.hide_timer()
        await self.score_ui.display()
        self.score_ui.subscribe("ui_gold_skips", self.command_skip_gold)
        self.score_ui.subscribe("ui_start_rmt", self.command_start_rmt)
        self.score_ui.subscribe("ui_stop_rmt", self.command_stop_rmt)

    async def command_start_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.HUB:
            self._map_completed = True
            self.game_status = RMTGame.GameStatus.RMT
            await self.chat(f'{player.nickname} started new RMT, loading next map ...')
            self.rmt_starter_player = player
            self._time_left = self._config.game_time_seconds
            self._mode_settings[S_TIME_LIMIT] = self._time_left
            if await self.load_with_retry():
                logger.info("RMT started")
                self.score_ui.game_started = True
            else:
                self.game_status = RMTGame.GameStatus.HUB
                self._mode_settings[S_TIME_LIMIT] = 0
                await self.chat("RMT failed to start")
            await self.mode_manager.update_settings(self._mode_settings)
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
            except Exception as e:
                logger.error("failed to load map...", exc_info=e)
                await self.map_handler.remove_loaded_map()

        return retry < max_retry

    async def command_stop_rmt(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.RMT:
            if player == self.rmt_starter_player:
                await self.chat(f'{player.nickname} stopped new RMT')
                await self.back_to_hub()
            else:
                await self.chat("you can't stop the RMT", player)
        else:
            await self.chat("RMT is not started yet")

    async def back_to_hub(self):
        if self.game_status == RMTGame.GameStatus.RMT:
            logger.info("Back to HUB ...")
            await self.hide_timer()
            self.score_ui.game_started = False
            self._score.rest()
            await self.score_ui.display()
            await self.map_handler.remove_loaded_map()
            await self.map_handler.load_hub()
            self.skipable_for_gold = False
            self.rmt_starter_player = None
            logger.info("Back to HUB completed")
            self.game_status = RMTGame.GameStatus.HUB

    async def map_begin_event(self, map, *args, **kwargs):
        logger.info("MAP Begin")
        self.map_handler.active_map = map
        self.score_ui.ui_tools_enabled = True
        if self.game_status == RMTGame.GameStatus.RMT:
            self._map_completed = False
            self.skipable_for_gold = False
            self.score_ui.game_started = True
            self._map_start_time = py_time.time()
        elif self.game_status == RMTGame.GameStatus.HUB:
            await self.hide_timer()
            self._map_completed = True
            self.score_ui.game_started = False

        await self.score_ui.display()

    async def map_end_event(self, time, count, *args, **kwargs):
        logger.info("MAP end")
        if self.game_status == RMTGame.GameStatus.RMT:
            self.skipable_for_gold = False
            self.score_ui.ui_tools_enabled = False
            if not self._map_completed:
                logger.info("RMT finished successfully")
                await self.chat(f'Challenge completed AT:{self._score.total_at} Gold:{self._score.total_gold}. peepoClap')
                await self.back_to_hub()
            else:
                self._mode_settings[S_TIME_LIMIT] = self._time_left
                logger.info("Continue with %d time left", self._time_left)
                await self.mode_manager.update_settings(self._mode_settings)

        await self.score_ui.display()

    async def on_map_finsh(self, player: Player, race_time: int, lap_time: int, cps, lap_cps, race_cps, flow,
                           is_end_race: bool, is_end_lap, raw, *args, **kwargs):
        logger.info(f'{player.nickname} has finished the map, {self.game_status} - {is_end_race} time: {race_time}ms')
        if self.game_status == RMTGame.GameStatus.RMT:
            await _lock.acquire()  # lock to avoid multiple AT before next map is loaded
            if self._map_completed:
                logger.info(f'[on_map_finish] Map was already completed')
                _lock.release()
                return

            if is_end_race:
                logger.info(f'[on_map_finish] Final time check for AT')
                if race_time <= self.map_handler.at_time:
                    logger.info(f'[on_map_finish] AT Time acquired')
                    self._update_time_left()
                    self._map_completed = True
                    await self.hide_timer()
                    _lock.release()  # with loading True don't need to lock
                    await self.chat(f'AT TIME, congratulations to {player.nickname}')
                    if await self.load_with_retry():
                        self._score.inc_at()
                    else:
                        await self.back_to_hub()
                elif race_time <= self.map_handler.gold_time:
                    logger.info(f'[on_map_finish] GOLD Time acquired')
                    self.skipable_for_gold = True
                    _lock.release()
                    await self.chat(f'GOLD TIME now {player.nickname} can /skip_gold to load next map')
                else:
                    logger.info(f'[on_map_finish] Normal Time acquired')
                    _lock.release()
            else:
                _lock.release()

    async def command_skip_gold(self, player: Player, *args, **kwargs):
        if self.game_status == RMTGame.GameStatus.RMT and not self._map_completed:
            if self.skipable_for_gold:
                if self.rmt_starter_player == player:
                    self._update_time_left()
                    self._map_completed = True
                    await self.chat(f'{player.nickname} decided to GOLD skip')
                    await self.hide_timer()
                    if await self.load_with_retry():
                        self.skipable_for_gold = False
                        self._score.inc_gold()
                    else:
                        await self.back_to_hub()
            else:
                await self.chat("Gold skip is not available", player)
        else:
            await self.chat("You are not allowed to skip", player)

    async def hide_timer(self):
        self._mode_settings[S_TIME_LIMIT] = 0
        await self.mode_manager.update_settings(self._mode_settings)

    def _update_time_left(self):
        self._time_left -= int(py_time.time() - self._map_start_time)
