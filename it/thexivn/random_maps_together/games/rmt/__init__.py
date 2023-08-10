import asyncio
import logging

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks
from pyplanet.utils.times import format_time


from .. import Game
from ...configuration import check_player_allowed_to_manage_running_game
from ...models.rmt.game_state import GameState
from ...models.enums.game_script import GameScript
from ...models.database.rmt.random_maps_together_score import RandomMapsTogetherScore
from ...models.database.rmt.random_maps_together_player_score import RandomMapsTogetherPlayerScore
from ...models.game_views.rmt import RandomMapsTogetherViews
from ...models.enums.game_modes import GameModes
from ...views.rmt.scoreboard import RandomMapsTogetherScoreBoardView
from ...constants import BIG_MESSAGE, RACE_SCORES_TABLE, S_FORCE_LAPS_NB, S_TIME_LIMIT
from ...configuration.rmt import RandomMapsTogetherConfiguration


_lock = asyncio.Lock()

# pyplanet.conf.settings.DEBUG = True

logger = logging.getLogger(__name__)

class RMTGame(Game):
    game_script = GameScript.TIME_ATTACK

    def __init__(self, app):
        super().__init__(app)
        self.config: RandomMapsTogetherConfiguration
        self.game_state: GameState
        self.score: RandomMapsTogetherScore
        self.views: RandomMapsTogetherViews = RandomMapsTogetherViews()
        self.app.mode_settings[S_FORCE_LAPS_NB] = -1

        self.views.scoreboard_view = RandomMapsTogetherScoreBoardView(self)
        mania_callback.player.player_connect.register(self.player_connect)
        mania_callback.player.player_disconnect.register(self.player_disconnect)

        logger.info("RMT Game initialized")

    def __del__(self):
        mania_callback.player.player_connect.unregister(self.player_connect)
        mania_callback.player.player_disconnect.unregister(self.player_disconnect)

    async def __aenter__(self):
        tm_callbacks.finish.register(self.on_map_finish)
        mania_callback.map.map_begin.register(self.map_begin_event)
        mania_callback.flow.round_end.register(self.map_end_event)
        tm_callbacks.start_line.register(self.round_start)

        await self.app.instance.gbx.multicall(
            self.app.instance.gbx.prepare('SetCallVoteRatios', [-1])
        )

        await self.set_original_scoreboard_visible(False)

        await self.views.settings_view.hide()

        self.config.map_generator.played_maps.clear()
        self.app.map_handler.next_map = None

        self.score = self.views.scoreboard_view.game_score = await RandomMapsTogetherScore.create(
            game_mode=self.game_mode.value,
            game_time_seconds=self.config.game_time_seconds,
            goal_medal=self.config.goal_medal.name,
            skip_medal=self.config.skip_medal.name,
        )
        self.game_state = GameState()

        self.config.update_player_configs()
        self.game_state.time_left = self.config.game_time_seconds
        self.app.mode_settings[S_TIME_LIMIT] = self.game_state.time_left
        await self.load_map_and_display_ingame_view()

        return self

    async def __aexit__(self, *err):
        if self.game_mode == GameModes.RANDOM_MAP_SURVIVAL:
            self.config.game_time_seconds += \
                self.config.skip_penalty_seconds * self.game_state.penalty_skips # type: ignore[attr-defined]
        await self.config.update_time_left()
        if self.game_state.time_left == 0 and self.score.medal_sum:
            self.score.total_time = self.game_state.round_timer.total_time
            await self.score.save()
        else:
            await self.score.destroy(recursive=True)
        self.game_state.current_map_completed = True
        await self.hide_timer()
        await self.views.scoreboard_view.display()
        await self.views.ingame_view.hide()
        asyncio.create_task(self._show_scoreboard_until_hub_map())
        await self.views.settings_view.display()

        tm_callbacks.finish.unregister(self.on_map_finish)
        mania_callback.map.map_begin.unregister(self.map_begin_event)
        mania_callback.flow.round_end.unregister(self.map_end_event)
        tm_callbacks.start_line.unregister(self.round_start)

        logger.info("Back to HUB completed")

    async def _show_scoreboard_until_hub_map(self):
        while self.app.map_handler.active_map.uid != self.app.map_handler.hub_map:
            await asyncio.sleep(1)
        await self.hide_custom_scoreboard()

    async def map_begin_event(self, *_args, **_kwargs):
        logger.info("[map_begin_event] STARTED")
        await self.set_original_scoreboard_visible(True)
        if self.app.map_handler.pre_patch_ice:
            await self.app.chat("$o$FB0 This track was created before the ICE physics change $z")
        self.game_state.current_map_completed = False
        asyncio.gather(
            self.app.map_handler.pre_load_next_map(),
            self.views.ingame_view.display(),
            self.views.scoreboard_view.hide(),
        )
        logger.info("[map_begin_event] ENDED")

    async def round_start(self, *_args, **_kwargs):
        self.game_state.round_timer.start_timer()

    async def map_end_event(self, *_args, **_kwargs):
        logger.info("MAP end")
        await self.set_original_scoreboard_visible(True)
        self.game_state.skip_medal_player = None
        self.game_state.skip_medal = None
        if not self.game_state.current_map_completed or self.game_state.time_left == 0:
            logger.info("%s finished successfully", self.game_mode.value)
            self.game_state.round_timer.stop_timer()
            await self.app.chat(
                "Challenge completed"
                f" {self.config.goal_medal.name}: {self.score.total_goal_medals}"
                f" {self.config.skip_medal.name}: {self.score.total_skip_medals}"
            )
            self.game_is_in_progress = False
        else:
            self.app.mode_settings[S_TIME_LIMIT] = round(self.game_state.time_left)
            logger.info("Continue with %d time left", self.game_state.time_left)
            await self.app.mode_manager.update_settings(self.app.mode_settings)

    async def on_map_finish(self, player: Player, race_time: int, lap_time: int, cps, lap_cps, race_cps, flow, # pylint: disable=too-many-locals,unused-argument
                           is_end_race: bool, is_end_lap, raw, *_args, **_kwargs): # pylint: disable=too-many-locals,unused-argument
        logger.info("[on_map_finish] %s has finished the map with time: %sms", player.nickname, race_time)
        async with _lock: # lock to avoid multiple AT before next map is loaded
            if self.game_state.current_map_completed:
                return logger.info('[on_map_finish] Map was already completed')

            if not is_end_race:
                return

            if self.game_state.is_paused:
                return await self.app.chat("Time doesn't count because game is paused", player)

            logger.info("[on_map_finish] Final time check for %s", self.config.goal_medal.name)
            race_medal = self.app.map_handler.get_medal_by_time(race_time)
            if not race_medal:
                return

            if race_medal >= (self.config.player_configs[player.login].goal_medal or self.config.goal_medal):
                if not (
                    self.config.player_configs[player.login].enabled
                    if self.config.player_configs[player.login].enabled is not None else self.config.enabled
                ):
                    return await self.app.chat(
                        f"{player.nickname} got {race_medal.name}, congratulations! Too bad it doesn't count.."
                    )

                logger.info("[on_map_finish %s acquired", self.config.goal_medal.name)
                self.game_state.round_timer.stop_timer()
                await self.config.update_time_left(goal_medal=True)

                self.score.total_goal_medals += 1
                self.score.medal_sum += race_medal.value
                self.score.save()

                player_score, _ = await RandomMapsTogetherPlayerScore.get_or_create(
                    game_score=self.score.id,
                    player=player.id,
                    defaults={
                        "goal_medal": getattr(self.config.player_configs[player.login].goal_medal, "name", None),
                        "skip_medal": getattr(self.config.player_configs[player.login].skip_medal, "name", None),
                    }
                )
                await player_score.increase_medal_count(race_medal)
                player_score.total_goal_medals += 1
                await player_score.save()

                self.game_state.current_map_completed = True
                await self.hide_timer()
                await self.app.chat(
                    f'{player.nickname} claimed {race_medal.name} with {format_time(race_time)}, congratulations!'
                )
                await self.load_map_and_display_ingame_view()
                await self.views.scoreboard_view.display()
                await self.views.ingame_view.hide()
            elif race_medal >= \
                (self.config.player_configs[player.login].skip_medal or self.config.skip_medal) \
                and not self.game_state.skip_medal:

                if not (
                    self.config.player_configs[player.login].enabled
                    if self.config.player_configs[player.login].enabled is not None else self.config.enabled
                ):
                    return await self.app.chat(
                        f"{player.nickname} got {race_medal.name}, "
                        "congratulations! Too bad it doesn't count.."
                    )

                logger.info('[on_map_finish] %s acquired', race_medal.name)
                self.game_state.skip_medal_player = player
                self.game_state.skip_medal = race_medal
                await self.views.ingame_view.display()
                await self.app.chat(
                    f'First {race_medal.name} acquired, '
                    f'congrats to {player.nickname} with {format_time(race_time)}'
                )
                await self.app.chat(f'You are now allowed to take the {race_medal.name} and skip the map')

    @check_player_allowed_to_manage_running_game
    async def command_skip_medal(self, player: Player, *_args, **_kwargs):
        if self.game_state.is_paused:
            return await self.app.chat("Game currently paused", player)
        if self.game_state.current_map_completed:
            return await self.app.chat("You are not allowed to skip", player)
        if not self.game_state.skip_medal_player:
            return await self.app.chat("No skip medal player available", player)
        if not self.game_state.skip_medal:
            return await self.app.chat(f"{self.config.skip_medal.name} skip is not available", player)

        self.game_state.round_timer.stop_timer()
        await self.config.update_time_left(skip_medal=True)

        self.score.total_skip_medals += 1
        self.score.medal_sum += self.game_state.skip_medal.value
        self.score.save()

        player_score, _ = await RandomMapsTogetherPlayerScore.get_or_create(
            game_score=self.score.id,
            player=self.game_state.skip_medal_player.id,
            defaults={
                "goal_medal": getattr(
                    self.config.player_configs[self.game_state.skip_medal_player.login].goal_medal, "name", None
                ),
                "skip_medal": getattr(
                    self.config.player_configs[self.game_state.skip_medal_player.login].skip_medal, "name", None
                ),
            }
        )
        player_score.total_skip_medals += 1
        await player_score.increase_medal_count(self.game_state.skip_medal)
        await player_score.save()

        self.game_state.current_map_completed = True
        await self.app.chat(
            f"{player.nickname} decided to take {self.game_state.skip_medal.name}"
            f" by {self.game_state.skip_medal_player.nickname} and skip"
        )

        await self.hide_timer()
        await self.load_map_and_display_ingame_view()
        await self.views.scoreboard_view.display()
        await self.views.ingame_view.hide()


    @check_player_allowed_to_manage_running_game
    async def command_skip(self, player: Player, *_args, **_kwargs):
        if self.game_state.is_paused:
            return await self.app.chat("Game currently paused", player)

        if self.game_state.current_map_completed:
            return await self.app.chat("You are not allowed to skip", player)

        if not self.config.can_skip_map():
            return await self.app.chat("No skip available", player)

        self.game_state.round_timer.stop_timer()
        await self.config.update_time_left(free_skip=True)
        self.game_state.current_map_completed = True

        await self.app.chat(f'{player.nickname} decided to skip the map')

        await self.hide_timer()
        await self.load_map_and_display_ingame_view()
        await self.views.scoreboard_view.display()
        await self.views.ingame_view.hide()

    @check_player_allowed_to_manage_running_game
    async def command_toggle_pause(self, *_args, **_kwargs):
        self.game_state.is_paused ^= True
        if self.game_state.is_paused:
            self.game_state.round_timer.stop_timer()
            self.game_state.time_left -= self.game_state.round_timer.last_round
            self.app.mode_settings[S_TIME_LIMIT] = 0
            await self.app.mode_manager.update_settings(self.app.mode_settings)
        else:
            self.app.mode_settings[S_TIME_LIMIT] = round(self.game_state.time_left)
            await self.app.mode_manager.update_settings(self.app.mode_settings)
            await self.app.map_handler.restart_map()
        await self.views.ingame_view.display()
        logging.info("Set paused: %s", str(self.game_state.is_paused))

    async def respawn_player(self, player: Player):
        # first, force mode 1 (spectator), then force mode 2 (player), then force mode 0 (user selectable)
        await self.app.instance.gbx('ForceSpectator', player.login, 1)
        await self.app.instance.gbx('ForceSpectator', player.login, 2)
        await self.app.instance.gbx('ForceSpectator', player.login, 0)

    async def hide_timer(self):
        self.app.mode_settings[S_TIME_LIMIT] = 0
        await self.app.mode_manager.update_settings(self.app.mode_settings)

    async def hide_custom_scoreboard(self, *_args, **_kwargs):
        await self.views.scoreboard_view.hide()
        await self.set_original_scoreboard_visible(True)

    async def set_original_scoreboard_visible(self, visible: bool):
        self.app.tm_ui_manager.properties.set_visibility(RACE_SCORES_TABLE, visible)
        self.app.tm_ui_manager.properties.set_visibility(BIG_MESSAGE, visible)
        await self.app.tm_ui_manager.properties.send_properties()

    async def player_connect(self, player: Player, is_spectator: bool, *_args, **_kwargs):
        if not is_spectator:
            self.config.update_player_configs()
            if self.game_is_in_progress:
                await self.views.ingame_view.display()
            else:
                await self.app.game_selector.display(player)
                await self.views.settings_view.display(player)

    async def player_disconnect(self, player: Player, *args, **kwargs):
        self.config.player_configs.pop(player.login, None)
