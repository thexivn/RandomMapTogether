import asyncio
import logging

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks
from pyplanet.utils.times import format_time


from .. import Game
from ...map_generator import MapGenerator
from ...models.chess.game_state import GameState
from ...models.database.chess.chess_score import ChessScore
from ...models.database.chess.chess_piece import ChessPiece
from ...models.game_views.chess import ChessViews
from ...views.chess.board import ChessBoardView
from ...views.chess.settings import ChessSettingsView
from ...views.chess.ingame import ChessIngameView
from ...constants import S_FORCE_LAPS_NB, S_TIME_LIMIT
from ...configuration.chess import ChessConfiguration
from ...models.enums.game_modes import GameModes
from ...models.enums.game_script import GameScript

logger = logging.getLogger(__name__)

class ChessGame(Game):
    game_mode = GameModes.CHESS
    game_script = GameScript.TEAM

    def __init__(self, app):
        super().__init__(app)
        self.config = ChessConfiguration(app, MapGenerator(app))
        self.config.update_player_configs()
        self.game_state: GameState
        self.score: ChessScore
        self.app.mode_settings[S_FORCE_LAPS_NB] = -1
        self.views: ChessViews = ChessViews()
        self.views.board_view = ChessBoardView(self)
        self.views.settings_view = ChessSettingsView(app, self.config)
        self.views.ingame_view = ChessIngameView(self)

        mania_callback.player.player_connect.register(self.player_connect)
        mania_callback.player.player_disconnect.register(self.player_disconnect)

        asyncio.gather(
            self.views.settings_view.display(),
        )

        logger.info("Chess Game initialized")

    def __del__(self):
        mania_callback.player.player_connect.unregister(self.player_connect)
        mania_callback.player.player_disconnect.unregister(self.player_disconnect)

    async def __aenter__(self):
        tm_callbacks.finish.register(self.on_map_finish)
        mania_callback.map.map_begin.register(self.map_begin_event)
        mania_callback.flow.round_end.register(self.map_end_event)

        await self.app.instance.gbx.multicall(
            self.app.instance.gbx.prepare('SetCallVoteRatios', [-1])
        )

        await self.views.settings_view.hide()

        self.config.map_generator.played_maps.clear()
        self.app.map_handler.next_map = None

        self.score = self.views.board_view.game_score = await ChessScore.create()
        self.game_state = GameState()
        for piece in self.game_state.pieces:
            piece.db, _ = await ChessPiece.get_or_create(
                game_score=self.score.id,
                team=piece.team.name,
                piece=piece.__class__.__name__.lower(),
                x=piece.x,
                y=piece.y
            )

        self.config.update_player_configs()
        try:
            await asyncio.gather(
                self.views.ingame_view.display()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to start Chess game: {str(exc)}") from exc

        return self

    async def __aexit__(self, *err):
        await self.score.destroy(recursive=True)
        await self.app.chat(f"Game ended in {self.game_state.state.value}")
        await self.views.ingame_view.hide()
        await self.views.board_view.hide()
        await self.views.settings_view.display()

        tm_callbacks.finish.unregister(self.on_map_finish)
        mania_callback.map.map_begin.unregister(self.map_begin_event)
        mania_callback.flow.round_end.unregister(self.map_end_event)

        logger.info("Back to HUB completed")

    async def map_begin_event(self, *_args, **_kwargs):
        logger.info("[map_begin_event] STARTED")
        if self.app.map_handler.pre_patch_ice:
            await self.app.chat("$o$FB0 This track was created before the ICE physics change $z")
        self.game_state.current_map_completed = False
        asyncio.gather(
            self.app.map_handler.pre_load_next_map(),
            self.views.ingame_view.display(),
            self.views.board_view.hide(),
        )
        logger.info("[map_begin_event] ENDED")

    async def map_end_event(self, *_args, **_kwargs):
        logger.info("MAP end")
        self.game_state.skip_medal_player = None
        self.game_state.skip_medal = None
        if not self.game_state.current_map_completed or self.game_state.time_left == 0:
            logger.info("%s finished successfully", self.game_mode.value)
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
        async with asyncio.Lock(): # lock to avoid multiple AT before next map is loaded
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
                await asyncio.gather(
                    self.app.map_handler.load_with_retry(),
                    self.views.ingame_view.display()
                )
                await self.views.board_view.display()
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

    async def respawn_player(self, player: Player):
        # first, force mode 1 (spectator), then force mode 2 (player), then force mode 0 (user selectable)
        await self.app.instance.gbx('ForceSpectator', player.login, 1)
        await self.app.instance.gbx('ForceSpectator', player.login, 2)
        await self.app.instance.gbx('ForceSpectator', player.login, 0)

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
