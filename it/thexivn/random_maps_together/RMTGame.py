import asyncio
import logging
import time as py_time
from threading import Thread

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.chat import ChatManager
from pyplanet.contrib.mode import ModeManager
from pyplanet.core.ui import GlobalUIManager

from . import MapHandler
from .Data.Configurations import RMCConfig, RMSConfig
from .Data.GameScore import GameScore
from .Data.GameState import GameState
from .Data.Medals import Medals
from .Data.GameModes import GameModes

from .views import RandomMapsTogetherView, RMTScoreBoard

BIG_MESSAGE = 'Race_BigMessage'

RACE_SCORES_TABLE = 'Race_ScoresTable'

S_TIME_LIMIT = 'S_TimeLimit'
S_FORCE_LAPS_NB = 'S_ForceLapsNb'
_lock = asyncio.Lock()

logger = logging.getLogger(__name__)


def background_loading_map(map_handler: MapHandler):
    logger.info("[background_loading_map] STARTED")
    map_handler.pre_load_next_map()
    logger.info("[background_loading_map] COMPLETED")


class RMTGame:
    def __init__(self, app, map_handler: MapHandler, chat: ChatManager, mode_manager: ModeManager,
                 score_ui: RandomMapsTogetherView, tm_ui_manager: GlobalUIManager):
        self.app = app
        self._rmt_starter_player: Player = None
        self._score = GameScore()
        self._map_handler = map_handler
        self._chat = chat
        self._mode_manager = mode_manager
        self._mode_settings = None
        self._map_start_time = py_time.time()
        self._time_left = self.app.app_settings.game_time_seconds
        self._score_ui = score_ui
        self._game_state = GameState()
        self._score_ui.set_score(self._score)
        self._score_ui.set_game_state(self._game_state)
        self._scoreboard_ui = RMTScoreBoard(self._score_ui.app, self._score, self._game_state)
        self._tm_ui = tm_ui_manager

        logger.info("RMT Game initialized")

    async def on_init(self):
        await self._map_handler.load_hub()
        logger.info("RMT Game loaded")
        self._mode_settings = await self._mode_manager.get_settings()
        self._mode_settings[S_FORCE_LAPS_NB] = int(-1)
        await self.hide_timer()
        await self._score_ui.display()
        self._score_ui.subscribe("ui_start_rmt", self.command_start_rmt)
        self._score_ui.subscribe("ui_stop_rmt", self.command_stop_rmt)
        self._score_ui.subscribe("ui_skip_medal", self.command_skip_medal)
        self._score_ui.subscribe("ui_free_skip", self.command_free_skip)

        self._score_ui.subscribe("ui_set_game_time_900", self.set_game_time_seconds)
        self._score_ui.subscribe("ui_set_game_time_1800", self.set_game_time_seconds)
        self._score_ui.subscribe("ui_set_game_time_3600", self.set_game_time_seconds)
        self._score_ui.subscribe("ui_set_game_time_7200", self.set_game_time_seconds)

        self._score_ui.subscribe("ui_set_goal_bonus_60", self.set_goal_bonus_seconds)
        self._score_ui.subscribe("ui_set_goal_bonus_180", self.set_goal_bonus_seconds)
        self._score_ui.subscribe("ui_set_goal_bonus_300", self.set_goal_bonus_seconds)

        self._score_ui.subscribe("ui_set_skip_penalty_30", self.set_skip_penalty_seconds)
        self._score_ui.subscribe("ui_set_skip_penalty_60", self.set_skip_penalty_seconds)
        self._score_ui.subscribe("ui_set_skip_penalty_120", self.set_skip_penalty_seconds)

        self._score_ui.subscribe("ui_set_goal_medal_author", self.set_goal_medal)
        self._score_ui.subscribe("ui_set_goal_medal_gold", self.set_goal_medal)
        self._score_ui.subscribe("ui_set_goal_medal_silver", self.set_goal_medal)

        self._score_ui.subscribe("ui_set_skip_medal_gold", self.set_skip_medal)
        self._score_ui.subscribe("ui_set_skip_medal_silver", self.set_skip_medal)
        self._score_ui.subscribe("ui_set_skip_medal_bronze", self.set_skip_medal)

        self._score_ui.subscribe("ui_toggle_infinite_skips", self.toggle_infinite_skips)

        self._score_ui.subscribe("ui_set_game_mode_rmc", self.set_game_mode_rmc)
        self._score_ui.subscribe("ui_set_game_mode_rms", self.set_game_mode_rms)

    async def command_start_rmt(self, player: Player, _, values, *args, **kwargs):
        if player.level < self.app.app_settings.min_level_to_start:
            await self._chat("You are not allowed to start the game", player)
            return

        if self._game_state.is_hub_stage():
            self.app.app_settings.game_time_seconds = int(values["game_time_seconds"])
            if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_SURVIVAL:
                self.app.app_settings.goal_bonus_seconds = int(values["goal_bonus_seconds"])
                self.app.app_settings.skip_penalty_seconds = int(values["skip_penalty_seconds"])

            self._score.goal_medal = self.app.app_settings.goal_medal
            self._score.skip_medal = self.app.app_settings.skip_medal

            self._game_state.set_start_new_state()
            await self._chat(f'{player.nickname} started new {self.app.app_settings.game_mode.value}, loading next map ...')
            self._rmt_starter_player = player
            self._time_left = self.app.app_settings.game_time_seconds
            self._mode_settings[S_TIME_LIMIT] = self._time_left
            if await self.load_with_retry():
                logger.info("RMT started")
                self._game_state.game_is_in_progress = True
            else:
                self._game_state.set_hub_state()
                self._mode_settings[S_TIME_LIMIT] = 0
                await self._chat(f"{self.app.app_settings.game_mode.value} RMT failed to start")
            await self._mode_manager.update_settings(self._mode_settings)
        else:
            await self._chat(f"{self.app.app_settings.game_mode.value} already started", player)

    async def load_with_retry(self, max_retry=3) -> bool:
        retry = 0
        load_succeeded = False
        self._game_state.map_is_loading = True
        await self._score_ui.display()
        while not load_succeeded and retry < max_retry:
            retry += 1
            try:
                await self._map_handler.load_next_map()
                load_succeeded = True
            except Exception as e:
                logger.error("failed to load map...", exc_info=e)
                await self._map_handler.remove_loaded_map()

        self._game_state.map_is_loading = False
        await self._score_ui.hide()
        return retry < max_retry

    async def command_stop_rmt(self, player: Player, *args, **kwargs):
        if self._game_state.is_game_stage():
            if await self._is_player_allowed_to_manage_running_game(player):
                await self._chat(f'{player.nickname} stopped the current session')
                await self.back_to_hub()
            else:
                await self._chat(f"You can't stop the {self.app.app_settings.game_mode.value}", player)
        else:
            await self._chat(f"{self.app.app_settings.game_mode.value} is not started yet", player)

    async def back_to_hub(self):
        if self._game_state.is_game_stage():
            logger.info("Back to HUB ...")
            await self.hide_timer()
            self._scoreboard_ui.set_time_left(0)
            self._game_state.set_hub_state()
            await self._scoreboard_ui.display()
            self._score.rest()
            await self._score_ui.hide()
            await self._map_handler.remove_loaded_map()
            await self._map_handler.load_hub()
            self._rmt_starter_player = None
            logger.info("Back to HUB completed")

    async def map_begin_event(self, map, *args, **kwargs):
        logger.info("[map_begin_event] STARTED")
        self._map_handler.active_map = map
        self._score_ui.ui_controls_visible = True
        if self._game_state.is_game_stage():
            if self._map_handler.pre_patch_ice:
                await self._chat("$o$FB0 This track was created before the ICE physics change $z"
                                 , self._rmt_starter_player)
            self._game_state.set_new_map_in_game_state()
            Thread(target=background_loading_map, args=[self._map_handler]).start()
        else:
            await self.hide_timer()
            self._game_state.current_map_completed = True

        await self._score_ui.display()
        logger.info("[map_begin_event] ENDED")

    async def map_end_event(self, time, count, *args, **kwargs):
        logger.info("MAP end")
        await self.set_original_scoreboard_visible(False)
        if self._game_state.is_game_stage():
            self._game_state.skip_medal_available = False
            self._game_state.skip_medal_player = None
            self._game_state.skip_medal = None
            self._score_ui.ui_controls_visible = False
            if not self._game_state.current_map_completed:
                logger.info(f"{self.app.app_settings.game_mode.value} finished successfully")
                await self._chat(
                    f'Challenge completed {self.app.app_settings.goal_medal.name}: {self._score.total_goal_medals} {self.app.app_settings.skip_medal.name}: {self._score.total_skip_medals}')
                await self.back_to_hub()
            else:
                self._mode_settings[S_TIME_LIMIT] = self._time_left
                logger.info("Continue with %d time left", self._time_left)
                await self._mode_manager.update_settings(self._mode_settings)


    async def on_map_finsh(self, player: Player, race_time: int, lap_time: int, cps, lap_cps, race_cps, flow,
                           is_end_race: bool, is_end_lap, raw, *args, **kwargs):
        logger.info(f'[on_map_finsh] {player.nickname} has finished the map with time: {race_time}ms')
        if self._game_state.is_game_stage():
            await _lock.acquire()  # lock to avoid multiple AT before next map is loaded
            if self._game_state.current_map_completed:
                logger.info(f'[on_map_finish] Map was already completed')
                _lock.release()
                return

            if is_end_race:
                logger.info(f'[on_map_finish] Final time check for {self.app.app_settings.goal_medal.name}')
                race_medal = self._map_handler.get_medal_by_time(race_time)
                if race_medal:
                    if race_medal >= self._score.goal_medal:
                        logger.info(f'[on_map_finish {self.app.app_settings.goal_medal.name} acquired')
                        self.app.app_settings.update_time_left(self, goal_medal=True)
                        self._game_state.set_map_completed_state()
                        await self.hide_timer()
                        _lock.release()  # with loading True don't need to lock
                        await self._chat(f'{player.nickname} claimed {self.app.app_settings.goal_medal.name}, congratulations!')
                        if await self.load_with_retry():
                            self._score.inc_medal_count(player, race_medal)
                            logger.info(f"{self._score.player_finishes[player.login]}")
                            await self._scoreboard_ui.display()
                            await self._score_ui.hide()
                        else:
                            await self.back_to_hub()
                    elif race_medal >= self._score.skip_medal and not self._game_state.skip_medal_available:
                        logger.info(f'[on_map_finish] {self.app.app_settings.skip_medal.name} acquired')
                        self._game_state.skip_medal_available = True
                        self._game_state.skip_medal_player = player
                        self._game_state.skip_medal = race_medal
                        _lock.release()
                        await self._score_ui.display()
                        await self._chat(f'First {self.app.app_settings.skip_medal.name} acquired, congrats to {player.nickname}')
                        await self._chat(f'You are now allowed to Take the {race_medal.name} and skip the map', self._rmt_starter_player)
                    else:
                        _lock.release()
                else:
                    _lock.release()
            else:
                _lock.release()

    async def command_skip_medal(self, player: Player, *args, **kwargs):
        if self._game_state.skip_command_allowed():
            if self._game_state.skip_medal_available:
                if await self._is_player_allowed_to_manage_running_game(player):
                    self.app.app_settings.update_time_left(self, skip_medal=True)
                    self._score.inc_medal_count(self._game_state.skip_medal_player, self._game_state.skip_medal)
                    self._game_state.set_map_completed_state()
                    await self._chat(f'{player.nickname} decided to {self.app.app_settings.skip_medal.name} skip')
                    await self.hide_timer()
                    if await self.load_with_retry():
                        await self._scoreboard_ui.display()
                        await self._score_ui.hide()
                    else:
                        await self.back_to_hub()
            else:
                await self._chat(f"{self.app.app_settings.skip_medal.name} skip is not available", player)
        else:
            await self._chat("You are not allowed to skip", player)

    async def command_free_skip(self, player: Player, *args, **kwargs):
        if self._game_state.skip_command_allowed():
            if self.app.app_settings.can_skip_map(self):
                if await self._is_player_allowed_to_manage_running_game(player):
                    self.app.app_settings.update_time_left(self, free_skip=True)
                    self._game_state.set_map_completed_state()
                    if not self._map_handler.pre_patch_ice and self._game_state.free_skip_available:
                        await self._chat(f'{player.nickname} decided to use free skip')
                        self._game_state.free_skip_available = False
                    else:
                        await self._chat(f'{player.nickname} decided to skip the map')
                    await self.hide_timer()
                    await self._scoreboard_ui.display()
                    await self._score_ui.hide()
                    if not await self.load_with_retry():
                        await self.back_to_hub()
            else:
                await self._chat("Free skip is not available", player)
        else:
            await self._chat("You are not allowed to skip", player)

    async def set_goal_bonus_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.goal_bonus_seconds = int(caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_goal_bonus_")[1])
            await self._score_ui.display()

    async def set_skip_penalty_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.skip_penalty_seconds = int(caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_skip_penalty_")[1])
            await self._score_ui.display()

    async def set_game_time_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.game_time_seconds = int(caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_game_time_")[1])
            await self._score_ui.display()

    async def set_goal_medal(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.goal_medal = Medals[caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_goal_medal_")[1].upper()]
            await self._score_ui.display()

    async def set_skip_medal(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.skip_medal = Medals[caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_skip_medal_")[1].upper()]
            await self._score_ui.display()

    async def toggle_infinite_skips(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.infinite_free_skips = not self.app.app_settings.infinite_free_skips
            await self._score_ui.display()

    async def set_game_mode_rmc(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings = RMCConfig()
            await self._score_ui.display()

    async def set_game_mode_rms(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings = RMSConfig()
            await self._score_ui.display()

    async def hide_timer(self):
        self._mode_settings[S_TIME_LIMIT] = 0
        await self._mode_manager.update_settings(self._mode_settings)

    async def _is_player_allowed_to_manage_running_game(self, player: Player) -> bool:
        if player.level == Player.LEVEL_MASTER or player == self._rmt_starter_player:
            return True
        await self._chat("You are not allowed manage running game", player)
        return False

    async def _check_player_allowed_to_change_game_settings(self, player: Player) -> bool:
        if player.level < self.app.app_settings.min_level_to_start:
            await self._chat("You are not allowed to change game settings", player)
            return False
        return True

    async def hide_custom_scoreboard(self, count, time, *args, **kwargs):
        await self._scoreboard_ui.hide()
        await self.set_original_scoreboard_visible(True)

    async def set_original_scoreboard_visible(self, visible: bool):
        self._tm_ui.properties.set_visibility(RACE_SCORES_TABLE, visible)
        self._tm_ui.properties.set_visibility(BIG_MESSAGE, visible)
        await self._tm_ui.properties.send_properties()

    async def set_time_left(self, count, time, *args, **kwargs):
        if self._game_state.is_game_stage():
            logger.info(f'ROUND_START {time} -- {count}')
            if not self._game_state.start_time:
                self._game_state.start_time = py_time.time()
            self._map_start_time = py_time.time()
