import asyncio
import logging
import threading
import time as py_time
from threading import Thread

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.contrib.chat import ChatManager
from pyplanet.contrib.mode import ModeManager
from pyplanet.core.ui import GlobalUIManager

from apps.it.thexivn.random_maps_together import MapHandler
from apps.it.thexivn.random_maps_together.Data.Configurations import Configurations
from apps.it.thexivn.random_maps_together.Data.GameScore import GameScore
from apps.it.thexivn.random_maps_together.Data.GameState import GameState
from pyplanet.utils.times import format_time
from apps.it.thexivn.random_maps_together.views import RandomMapsTogetherView, RMTScoreBoard, PollView, PollUpdaterView
from pyplanet.views.generics import ask_confirmation

BIG_MESSAGE = 'Race_BigMessage'

RACE_SCORES_TABLE = 'Race_ScoresTable'

S_TIME_LIMIT = 'S_TimeLimit'
S_FORCE_LAPS_NB = 'S_ForceLapsNb'
_lock = asyncio.Lock()

logger = logging.getLogger(__name__)
tmx_tags = [
    {"ID": 0, "Name": "ALL RANDOM", "Color": ""},
    {"ID": 1, "Name": "Race", "Color": ""}, {"ID": 2, "Name": "FullSpeed", "Color": ""},
    {"ID": 3, "Name": "Tech", "Color": ""}, {"ID": 4, "Name": "RPG", "Color": ""},
    {"ID": 5, "Name": "LOL", "Color": ""}, {"ID": 6, "Name": "Press Forward", "Color": ""},
    {"ID": 7, "Name": "SpeedTech", "Color": ""}, {"ID": 8, "Name": "MultiLap", "Color": ""},
    {"ID": 9, "Name": "Offroad", "Color": "705100"}, {"ID": 10, "Name": "Trial", "Color": ""},
    {"ID": 11, "Name": "ZrT", "Color": "1a6300"}, {"ID": 12, "Name": "SpeedFun", "Color": ""},
    {"ID": 13, "Name": "Competitive", "Color": ""}, {"ID": 14, "Name": "Ice", "Color": "05767d"},
    {"ID": 15, "Name": "Dirt", "Color": "5e2d09"}, {"ID": 16, "Name": "Stunt", "Color": ""},
    {"ID": 17, "Name": "Reactor", "Color": "d04500"}, {"ID": 18, "Name": "Platform", "Color": ""},
    {"ID": 19, "Name": "Slow Motion", "Color": "004388"}, {"ID": 20, "Name": "Bumper", "Color": "aa0000"},
    {"ID": 21, "Name": "Fragile", "Color": "993366"}, {"ID": 22, "Name": "Scenery", "Color": ""},
    {"ID": 23, "Name": "Kacky", "Color": ""}, {"ID": 24, "Name": "Endurance", "Color": ""},
    {"ID": 25, "Name": "Mini", "Color": ""}, {"ID": 26, "Name": "Remake", "Color": ""},
    {"ID": 27, "Name": "Mixed", "Color": ""}, {"ID": 28, "Name": "Nascar", "Color": ""},
    {"ID": 29, "Name": "SpeedDrift", "Color": ""}, {"ID": 30, "Name": "Minigame", "Color": "7e0e69"},
    {"ID": 31, "Name": "Obstacle", "Color": ""}, {"ID": 32, "Name": "Transitional", "Color": ""},
    {"ID": 33, "Name": "Grass", "Color": "06a805"}, {"ID": 34, "Name": "Backwards", "Color": "83aa00"},
    {"ID": 35, "Name": "Freewheel", "Color": "f2384e"}, {"ID": 36, "Name": "Signature", "Color": "f1c438"},
    {"ID": 37, "Name": "Royal", "Color": "ff0010"}, {"ID": 38, "Name": "Water", "Color": "69dbff"},
    {"ID": 39, "Name": "Plastic", "Color": "fffc00"}, {"ID": 40, "Name": "Arena", "Color": ""},
    {"ID": 41, "Name": "Freestyle", "Color": ""}, {"ID": 42, "Name": "Educational", "Color": ""},
    {"ID": 43, "Name": "Sausage", "Color": ""}, {"ID": 44, "Name": "Bobsleigh", "Color": ""},
    {"ID": 45, "Name": "Pathfinding", "Color": ""}, {"ID": 46, "Name": "FlagRush", "Color": "7a0000"},
    {"ID": 47, "Name": "Puzzle", "Color": "459873"}, {"ID": 48, "Name": "Freeblocking", "Color": "ffffff"},
    {"ID": 49, "Name": "Altered Nadeo", "Color": "3a3a3a"}, {"ID": 50, "Name": "SnowCar", "Color": "d3d3d3"},
    {"ID": 51, "Name": "Wood", "Color": "814b00"}, {"ID": 52, "Name": "Underwater", "Color": "03afff"},
    {"ID": 53, "Name": "Turtle", "Color": "6bb74e"},
]

def get_tag(id):
    for tag in tmx_tags:
        if tag['ID'] == id:
            return tag['Name']
    return ""


def background_loading_map(map_handler: MapHandler):
    logger.info("[background_loading_map] STARTED")
    map_handler.pre_load_next_map()
    logger.info("[background_loading_map] COMPLETED")


class RMTGame:
    def __init__(self, map_handler: MapHandler, chat: ChatManager, mode_manager: ModeManager,
                 score_ui: RandomMapsTogetherView, config: Configurations, tm_ui_manager: GlobalUIManager, ui_manager):
        self._rmt_starter_player: Player = None
        self._score = GameScore()
        self._map_handler = map_handler
        self._chat = chat
        self._mode_manager = mode_manager
        self._mode_settings = None
        self._map_start_time = py_time.time()
        self._config = config
        self._time_left = config.game_time_seconds
        self._score_ui = score_ui
        self._game_state = GameState()
        self._score_ui.set_score(self._score)
        self._score_ui.set_game_state(self._game_state)
        self.scoreboard_ui = RMTScoreBoard(self._score_ui.app, self._score)
        self._tm_ui = tm_ui_manager
        self.poll_votes = {}
        self.poll_time = 0
        self.poll_updater_widget = PollUpdaterView(self, ui_manager)
        self.poll_widget = PollView(self, ui_manager)
        logger.info("RMT Game initialized")

    async def on_init(self):
        await self._map_handler.load_hub()
        logger.info("RMT Game loaded")
        self._mode_settings = await self._mode_manager.get_settings()
        self._mode_settings[S_FORCE_LAPS_NB] = int(-1)
        await self.hide_timer()
        await self.scoreboard_ui.display()
        await self._score_ui.display()
        self.poll_widget.subscribe("vote", self.poll_do_vote)
        self._score_ui.subscribe("ui_gold_skips", self.command_skip_gold)
        self._score_ui.subscribe("ui_start_rmt", self.command_start_rmt)
        self._score_ui.subscribe("ui_stop_rmt", self.command_stop_rmt)
        self._score_ui.subscribe("ui_free_skip", self.command_free_skip)

    async def command_start_rmt(self, player: Player, *args, **kwargs):
        if player.level < self._config.min_level_to_start:
            await self._chat("you are not allowed to start the game", player)
            return

        if self._game_state.is_hub_stage():
            self._game_state.set_start_new_state()
            await self._chat(f'{player.nickname}$z$s started a new RMT, loading next map ...')
            self._rmt_starter_player = player
            self._time_left = self._config.game_time_seconds
            self._mode_settings[S_TIME_LIMIT] = self._time_left
            if await self.load_with_retry():
                logger.info("RMT started")
                self._game_state.game_is_in_progress = True
            else:
                self._game_state.set_hub_state()
                self._mode_settings[S_TIME_LIMIT] = 0
                await self._chat("RMT failed to start")
            await self._mode_manager.update_settings(self._mode_settings)
        else:
            await self._chat("RMT already started", player)

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
            if self._is_player_allowed(player):
                await self._chat(f'{player.nickname}$z$s stopped the RMT session!')
                await self.back_to_hub()
            else:
                await self._chat("You can't stop the RMT", player)
        else:
            await self._chat("RMT is not started yet", player)

    async def back_to_hub(self):
        if self._game_state.is_game_stage():
            logger.info("Back to HUB ...")
            await self.hide_timer()
            self.scoreboard_ui.set_time_left(0)
            self._game_state.set_hub_state()
            # await self._scoreboard_ui.display()
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
            if self._map_handler.current_map_is_skipable:
                await self._chat("$o$FB0 this track was created before the ICE physics change $z")

            self._game_state.set_new_map_in_game_state()
            Thread(target=background_loading_map, args=[self._map_handler]).start()
            self._score_ui.set_skippable_map(self._can_skip_map())
        else:
            await self.hide_timer()
            self._game_state.current_map_completed = True

        await self._score_ui.display()
        logger.info("[map_begin_event] ENDED")

    async def map_end_event(self, time, count, *args, **kwargs):
        logger.info("MAP end")
        await self.set_original_scoreboard_visible(False)
        if self._game_state.is_game_stage():
            self._game_state.gold_skip_available = False
            self._score_ui.ui_controls_visible = False
            if not self._game_state.current_map_completed:
                logger.info("RMT finished successfully")
                await self._chat(
                    f'Challenge completed AT:{self._score.total_at} Gold:{self._score.total_gold}. peepoClap')
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
                logger.info(f'[on_map_finish] Final time check for AT')
                if race_time <= self._map_handler.at_time:
                    logger.info(f'[on_map_finish] AT Time acquired')
                    self._update_time_left()
                    self._game_state.set_map_completed_state()
                    await self.hide_timer()
                    _lock.release()  # with loading True don't need to lock
                    await self._chat(f'Author Time Reached! Congrats to {player.nickname}')
                    if await self.load_with_retry():
                        self._score.inc_at(player)
                        await self.scoreboard_ui.display()
                        await self._score_ui.hide()
                    else:
                        await self.back_to_hub()
                elif race_time <= self._map_handler.gold_time and not self._game_state.gold_skip_available:
                    logger.info(f'[on_map_finish] GOLD Time acquired')
                    self._game_state.gold_skip_available = True
                    _lock.release()
                    await self._score_ui.display()
                    await self._chat(f'Gold Time acquired! Congrats to {player.nickname}')
                    await self._chat('You are allowed to Take the GOLD and skip the map. Use /gold_skip to start vote!')
                else:
                    _lock.release()
            else:
                _lock.release()

    async def command_skip_gold(self, player: Player, *args, **kwargs):
        if self._game_state.skip_command_allowed():
            if self._game_state.gold_skip_available:
                if self._is_player_allowed(player):
                    self._update_time_left()
                    self._game_state.set_map_completed_state()
                    await self._chat(f'Admin decided to GOLD skip')
                    await self.hide_timer()
                    if await self.load_with_retry():
                        self._score.inc_gold()
                        await self.scoreboard_ui.display()
                        await self._score_ui.hide()
                    else:
                        await self.back_to_hub()
            else:
                await self._chat("Gold skip is not available", player)
        else:
            await self._chat("You are not allowed to skip", player)

    def get_gold_skip_allowed(self):
        return self._game_state.skip_command_allowed() and self._game_state.gold_skip_available

    def get_free_skip_allowed(self):
        return self._game_state.skip_command_allowed() and self._can_skip_map()

    async def command_vote_skip_gold(self, *args, **kwargs):
        if self._game_state.gold_skip_available:
            self._update_time_left()
            self._game_state.set_map_completed_state()
            await self._chat(f'Players decided to GOLD skip')
            await self.hide_timer()
            if await self.load_with_retry():
                self._score.inc_gold()
                await self.scoreboard_ui.display()
                await self._score_ui.hide()
            else:
                await self.back_to_hub()
        else:
            await self._chat("Gold skip is not available")

    async def command_free_skip(self, player: Player, *args, **kwargs):
        cancel = bool(
            await ask_confirmation(
                player=player,
                message=f'Force free skip? You sure?',
                buttons=[{"name": "Yeah, do it!"}, {"name": "Nope"}],
            )
        )
        if not cancel:
            if self._game_state.skip_command_allowed():
                if self._can_skip_map():
                    if self._is_player_allowed(player):
                        self._update_time_left()
                        self._game_state.set_map_completed_state()
                        if not self._map_handler.current_map_is_skipable:
                            self._game_state.free_skip_available = False
                        await self._chat(f'Admin decided to skip the map')
                        await self.hide_timer()
                        await self.scoreboard_ui.display()
                        await self._score_ui.hide()
                        if not await self.load_with_retry():
                            await self.back_to_hub()
                else:
                    await self._chat("Free skip is not available", player)
            else:
                await self._chat("You are not allowed to skip", player)

    async def command_vote_free_skip(self, *args, **kwargs):
        if self._can_skip_map():
            self._update_time_left()
            self._game_state.set_map_completed_state()
            if not self._map_handler.current_map_is_skipable:
                self._game_state.free_skip_available = False
            await self._chat(f'Players decided to skip the map')
            await self.hide_timer()
            await self.scoreboard_ui.display()
            await self._score_ui.hide()
            if not await self.load_with_retry():
                await self.back_to_hub()
        else:
            await self._chat("Free skip is not available")

    async def command_poll(self, player: Player, *args, **kwargs):
        if player.level < 1:
            await self._chat("Not allowed", player)
            return
        self.poll_votes = []
        for tag in tmx_tags:
            self.poll_votes.append({"ID": tag['ID'], "Name": tag['Name'], "Vote": 0 })

        self.poll_time = int(py_time.time() + 60)
        await self.poll_widget.display()
        asyncio.ensure_future(self.poll_updater())

    async def poll_result(self):
        items = sorted(self.poll_votes, key=lambda x: x['Vote'], reverse=True)
        i = 0
        out = ""
        for item in items:
            if i >= 3:
                break
            if item['Vote'] > 0:
                out += f"$fff$o{item['Vote']}$o  $0af{item['Name']}({item['ID']}),  "
            i += 1
        await self._chat("Top Votes: " + out)

    async def poll_do_vote(self, player: Player, raw, entries, *args, **kwargs):
        for item in self.poll_votes:
            if item['ID'] == int(entries['tag']):
                item['Vote'] += 1

    async def poll_updater(self):
        timeleft = int(self.poll_time - py_time.time())
        if timeleft > 0:
            await self.poll_updater_widget.display()
            await asyncio.sleep(1)
            asyncio.ensure_future(self.poll_updater())
        else:
            await self.poll_updater_widget.hide()
            await self.poll_widget.hide()
            await self.poll_result()

    async def hide_timer(self):
        self._mode_settings[S_TIME_LIMIT] = 0
        await self._mode_manager.update_settings(self._mode_settings)

    def _update_time_left(self):
        self._time_left -= int(py_time.time() - self._map_start_time)
        self.scoreboard_ui.set_time_left(self._time_left)

    def _is_player_allowed(self, player: Player) -> bool:
        return player.level == Player.LEVEL_OPERATOR or player == self._rmt_starter_player

    async def hide_custom_scoreboard(self, count, time, *args, **kwargs):
        pass
        # await self._scoreboard_ui.hide()
        # await self.set_original_scoreboard_visible(True)

    async def set_original_scoreboard_visible(self, visible: bool):
        pass
        # self._tm_ui.properties.set_visibility(RACE_SCORES_TABLE, visible)
        # self._tm_ui.properties.set_visibility(BIG_MESSAGE, visible)
        # await self._tm_ui.properties.send_properties()

    async def set_time_left(self, count, time, *args, **kwargs):
        if self._game_state.is_game_stage():
            logger.info(f'ROUND_START {time} -- {count}')
            self._map_start_time = py_time.time()
            tags = []
            for tag in self._map_handler.current_map.tags:
                tags.append(get_tag(tag) + f"({tag})")
            await self._chat(f"Author Time: {format_time(self._map_handler.current_map.author_time)}")
            await self._chat(f"Tags: {', '.join(tags)}")

    def _can_skip_map(self) -> bool:
        return self._game_state.free_skip_available or \
            self._config.infinite_free_skips or \
            self._map_handler.current_map_is_skipable
