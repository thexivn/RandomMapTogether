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
from .Data.GameModes import GameModes
from .Data.Medals import Medals
from .map_generator import MapGenerator
from .map_generator.map_pack import MapPack
from .map_generator.totd import TOTD

from .views import RandomMapsTogetherView, RMTScoreBoard, PlayerConfigsView, prompt_for_input

BIG_MESSAGE = 'Race_BigMessage'

RACE_SCORES_TABLE = 'Race_ScoresTable'

S_TIME_LIMIT = 'S_TimeLimit'
S_FORCE_LAPS_NB = 'S_ForceLapsNb'
S_CHAT_TIME = 'S_ChatTime'
_lock = asyncio.Lock()

# pyplanet.conf.settings.DEBUG = True

logger = logging.getLogger(__name__)


async def background_loading_map(map_handler: MapHandler):
    logger.info("[background_loading_map] STARTED")
    await map_handler.pre_load_next_map()
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
        self._scoreboard_ui = RMTScoreBoard(app, self._score, self._game_state, self)
        self._player_configs_ui = PlayerConfigsView(app)
        self._tm_ui = tm_ui_manager
        self._time_left_at_pause = 83
        self._time_at_pause = py_time.time()
        logger.info("RMT Game initialized")

    async def on_init(self):
        await self._map_handler.load_hub()
        logger.info("RMT Game loaded")
        self._mode_settings = await self._mode_manager.get_settings()
        self._mode_settings[S_FORCE_LAPS_NB] = int(-1)
        asyncio.create_task(background_loading_map(self._map_handler))
        # self._mode_settings[S_CHAT_TIME] = int(1)
        await self.hide_timer()
        await self._score_ui.display()
        self._score_ui.subscribe("ui_start_rmt", self.command_start_rmt)
        self._score_ui.subscribe("ui_stop_rmt", self.command_stop_rmt)
        self._score_ui.subscribe("ui_skip_medal", self.command_skip_medal)
        self._score_ui.subscribe("ui_free_skip", self.command_free_skip)
        self._score_ui.subscribe("ui_toggle_pause", self.command_toggle_pause)
        self._score_ui.subscribe("ui_toggle_scoreboard", self.command_toggle_scoreboard)

        self._score_ui.subscribe("ui_set_game_time_seconds", self.set_game_time_seconds)
        self._score_ui.subscribe("ui_set_goal_bonus_seconds", self.set_goal_bonus_seconds)
        self._score_ui.subscribe("ui_set_skip_penalty_seconds", self.set_skip_penalty_seconds)

        self._score_ui.subscribe("ui_set_goal_medal_author", self.set_goal_medal)
        self._score_ui.subscribe("ui_set_goal_medal_gold", self.set_goal_medal)
        self._score_ui.subscribe("ui_set_goal_medal_silver", self.set_goal_medal)

        self._score_ui.subscribe("ui_set_skip_medal_gold", self.set_skip_medal)
        self._score_ui.subscribe("ui_set_skip_medal_silver", self.set_skip_medal)
        self._score_ui.subscribe("ui_set_skip_medal_bronze", self.set_skip_medal)

        self._score_ui.subscribe("ui_set_map_generator_random", self.set_map_generator)
        self._score_ui.subscribe("ui_set_map_generator_totd", self.set_map_generator)
        self._score_ui.subscribe("ui_set_map_generator_map_pack", self.set_map_generator)
        self._score_ui.subscribe("ui_set_map_pack_id", self.set_map_pack_id)

        self._score_ui.subscribe("ui_toggle_infinite_skips", self.toggle_infinite_skips)
        self._score_ui.subscribe("ui_toggle_allow_pausing", self.toggle_allow_pausing)

        self._score_ui.subscribe("ui_set_game_mode_rmc", self.set_game_mode_rmc)
        self._score_ui.subscribe("ui_set_game_mode_rms", self.set_game_mode_rms)

        self._score_ui.subscribe("ui_toggle_enabled_players", self.toggle_enabled_players)

        self._score_ui.subscribe("ui_toggle_player_settings", self.toggle_player_settings)

        asyncio.ensure_future(self.update_ui_loop())

    async def update_ui_loop(self):
        while True:
            await asyncio.sleep(0.25)
            if self._game_state.game_is_in_progress:
                if self._scoreboard_ui._is_global_shown:
                    await self._scoreboard_ui.display()
                elif len(self._scoreboard_ui._is_player_shown) > 0:
                    await self._scoreboard_ui.display(self._scoreboard_ui._is_player_shown.keys())
            self.app.app_settings.update_player_configs()

    async def command_start_rmt(self, player: Player, _, values, *args, **kwargs):
        if player.level < self.app.app_settings.min_level_to_start:
            await self._chat("You are not allowed to start the game", player)
            return

        await self._score_ui.hide()
        await self._scoreboard_ui.display()

        if self._game_state.is_hub_stage():
            self.app.app_settings.update_player_configs()
            self._map_handler.map_generator = self.app.app_settings.map_generator
            self._game_state.set_start_new_state()
            await self._chat(f'{player.nickname} started new {self.app.app_settings.game_mode.value}, loading next map ...')
            logger.info(self.app.app_settings.map_generator)
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

        self._game_state.map_is_loading = False

        # await self._score_ui.hide()
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
            self._chat('Game over -- Returning to HUB')
            logger.info("Back to HUB ...")
            # self._time_left = 0
            await self.hide_timer()
            self._game_state.set_hub_state()
            await self._scoreboard_ui.display()
            self._score.rest()
            await self._score_ui.hide()
            await self._map_handler.load_hub()
            await background_loading_map(self._map_handler)

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
            asyncio.create_task(background_loading_map(self._map_handler))
        else:
            await self.hide_timer()
            self._game_state.current_map_completed = True

        await self._score_ui.display()
        logger.info("[map_begin_event] ENDED")

    async def map_end_event(self, time, count, *args, **kwargs):
        logger.info("MAP end")
        await self.set_original_scoreboard_visible(False)
        if self._game_state.is_game_stage():
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


    async def on_map_finish(self, player: Player, race_time: int, lap_time: int, cps, lap_cps, race_cps, flow,
                           is_end_race: bool, is_end_lap, raw, *args, **kwargs):
        logger.info(f'[on_map_finish] {player.nickname} has finished the map with time: {race_time}ms')
        if self._game_state.is_game_stage():
            async with _lock: # lock to avoid multiple AT before next map is loaded
                if self._game_state.current_map_completed:
                    logger.info(f'[on_map_finish] Map was already completed')
                    return

                if is_end_race:
                    logger.info(f'[on_map_finish] Final time check for {self.app.app_settings.goal_medal.value}')

                    if self._game_state.is_paused:
                        return await self._chat("Time doesn't count because game is paused", player)
                    if (py_time.time() - (race_time * 0.001)) < self._time_at_pause:
                        return await self._chat(f"Time doesn't count because game was paused ({race_time}ms / cur time: {py_time.time()} / paused at time: {self._time_at_pause})", player)

                    logger.info(f'[on_map_finish] Final time check for {self.app.app_settings.goal_medal.name}')
                    race_medal = self._map_handler.get_medal_by_time(race_time)
                    if race_medal:
                        if race_medal >= self.app.app_settings.player_configs[player.login].goal_medal:
                            if not self.app.app_settings.player_configs[player.login].enabled:
                                return await self._chat(f"{player.nickname} got {race_medal.name}, congratulations! Too bad it doesn't count..")
                            logger.info(f'[on_map_finish {self.app.app_settings.goal_medal.name} acquired')
                            self.app.app_settings.update_time_left(self, goal_medal=True)
                            self._game_state.set_map_completed_state()
                            await self.hide_timer()
                            await self._chat(f'{player.nickname} claimed {race_medal.name}, congratulations!')
                            if await self.load_with_retry():
                                self._score.inc_medal_count(player, race_medal, goal_medal=True)
                                logger.info(f"{self._score.player_finishes[player.login]}")
                                await self._scoreboard_ui.display()
                                await self._score_ui.hide()
                            else:
                                await self.back_to_hub()
                        elif race_medal >= self.app.app_settings.player_configs[player.login].skip_medal and not self._game_state.skip_medal:
                            if not self.app.app_settings.player_configs[player.login].enabled:
                                return await self._chat(f"{player.nickname} got {race_medal.name}, congratulations! Too bad it doesn't count..")
                            logger.info(f'[on_map_finish] {race_medal.name} acquired')
                            self._game_state.skip_medal_player = player
                            self._game_state.skip_medal = race_medal
                            await self._score_ui.display()
                            await self._chat(f'First {race_medal.name} acquired, congrats to {player.nickname}')
                            await self._chat(f'You are now allowed to take the {race_medal.name} and skip the map', self._rmt_starter_player)

    async def command_skip_medal(self, player: Player, *args, **kwargs):
        if self._game_state.is_paused:
            return await self._chat("Game currently paused", player)
        if self._game_state.skip_command_allowed():
            if self._game_state.skip_medal:
                if await self._is_player_allowed_to_manage_running_game(player):
                    self.app.app_settings.update_time_left(self, skip_medal=True)
                    self._score.inc_medal_count(self._game_state.skip_medal_player, self._game_state.skip_medal, skip_medal=True)
                    self._game_state.set_map_completed_state()
                    await self._chat(f'{player.nickname} decided to take {self._game_state.skip_medal.name} by {self._game_state.skip_medal_player.nickname} and skip')
                    await self.hide_timer()
                    if await self.load_with_retry():
                        logging.info(f"Loading next map success")
                        await self._scoreboard_ui.display()
                        await self._score_ui.hide()
                        logging.info(f"Loading next map UI updated")
                    else:
                        await self.back_to_hub()
            else:
                await self._chat(f"{self.app.app_settings.skip_medal.name} skip is not available", player)
        else:
            await self._chat("You are not allowed to skip", player)

    async def command_free_skip(self, player: Player, *args, **kwargs):
        if self._game_state.is_paused:
            return await self._chat("Game currently paused", player)
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
                        logging.info(f"Skipping map success")
            else:
                await self._chat("Free skip is not available", player)
        else:
            await self._chat("You are not allowed to skip", player)

    async def command_toggle_pause(self, player: Player, *args, **kwargs):
        if not self.app.app_settings.allow_pausing or not await self._is_player_allowed_to_manage_running_game(player):
            return await self._chat("Cannot toggle pause", player)
        self._game_state.is_paused ^= True
        pause_duration = 0
        if self._game_state.is_paused:
            self._time_at_pause = py_time.time()
            self._time_left_at_pause = self._time_left
            self._mode_settings[S_TIME_LIMIT] = -1
        else:
            pause_duration = int(py_time.time() - self._time_at_pause + .5)
            self._mode_settings[S_TIME_LIMIT] = self._time_left_at_pause + pause_duration
            self._time_left += pause_duration
            # respawn the player, this means the unpausing player's next run always starts after unpausing.
            await self.respawn_player(player)
        await self._mode_manager.update_settings(self._mode_settings)
        await self._score_ui.display()
        # no need to extend b/c this is done by setting the time limit to whatever it was + pause duration
        # if pause_duration > 0:
        #     await self._map_handler._map_manager.extend_ta(pause_duration)
        logging.info(f"Set paused: " + str(self._game_state.is_paused))

    async def command_toggle_scoreboard(self, player: Player, *args, **kw):
        await self._scoreboard_ui.toggle_for(player.login)

    async def respawn_player(self, player: Player):
        # first, force mode 1 (spectator), then force mode 2 (player), then force mode 0 (user selectable)
        await self._mode_manager._instance.gbx('ForceSpectator', player.login, 1)
        await self._mode_manager._instance.gbx('ForceSpectator', player.login, 2)
        await self._mode_manager._instance.gbx('ForceSpectator', player.login, 0)

    async def set_goal_bonus_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            buttons = [
                {"name": "1m", "value": 60},
                {"name": "3m", "value": 180},
                {"name": "5m", "value": 300}
            ]
            time_seconds = await prompt_for_input(player, "Goal bonus in seconds", buttons)
            self.app.app_settings.goal_bonus_seconds = int(time_seconds)

            await self._score_ui.display()

    async def set_skip_penalty_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            buttons = [
                {"name": "30s", "value": 30},
                {"name": "1m", "value": 60},
                {"name": "2m", "value": 120}
            ]
            time_seconds = await prompt_for_input(player, "Skip penalty in seconds", buttons)
            self.app.app_settings.skip_penalty_seconds = int(time_seconds)

            await self._score_ui.display()

    async def set_game_time_seconds(self, player: Player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            buttons = [
                {"name": "30m", "value": 1800},
                {"name": "1h", "value": 3600},
                {"name": "2h", "value": 7200}
            ] if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_CHALLENGE else [
                {"name": "15m", "value": 900},
                {"name": "30m", "value": 1800},
                {"name": "1h", "value": 3600}
            ]
            time_seconds = await prompt_for_input(player, "Game time in seconds", buttons)
            self.app.app_settings.game_time_seconds = int(time_seconds)

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
            self.app.app_settings.infinite_free_skips ^= True
            await self._score_ui.display()

    async def toggle_allow_pausing(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.allow_pausing ^= True
            await self._score_ui.display()

    async def set_game_mode_rmc(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings = RMCConfig(self.app)
            await self._score_ui.display()

    async def set_game_mode_rms(self, player: Player, *args, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings = RMSConfig(self.app)
            await self._score_ui.display()

    async def set_map_generator(self, player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            map_generator_string = caller.split("it_thexivn_RandomMapsTogether_widget__ui_set_map_generator_")[1]
            if map_generator_string == "random":
                self.app.app_settings.map_generator = MapGenerator()
            elif map_generator_string == "totd":
                self.app.app_settings.map_generator = TOTD()
            elif map_generator_string == "map_pack":
                self.app.app_settings.map_generator = MapPack()
                await self.set_map_pack_id(player, caller, values, **kwargs)
            await self._score_ui.display()

    async def set_map_pack_id(self, player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            map_pack_id = await prompt_for_input(player, "Map Pack ID")
            self.app.app_settings.map_generator.map_pack_id = int(map_pack_id)
            await self._score_ui.display()

    async def toggle_player_settings(self, player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            await self._player_configs_ui.display(player)
            logger.info(self.app.app_settings.player_configs)

    async def toggle_enabled_players(self, player, caller, values, **kwargs):
        if await self._check_player_allowed_to_change_game_settings(player):
            self.app.app_settings.enabled ^= True
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

    def time_left_str(self):
        tl = self._time_left
        if tl == 0:
            return "00:00:00"
        if self._game_state.is_paused:
            pause_duration = int(py_time.time() - self._time_at_pause + .5)
            tl = self._time_left_at_pause + pause_duration
        if not self._game_state.map_is_loading and not self._game_state.current_map_completed:
            tl -= int(py_time.time() - self._map_start_time + .5)
        return py_time.strftime('%H:%M:%S', py_time.gmtime(tl))
