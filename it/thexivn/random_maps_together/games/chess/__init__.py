import asyncio
import logging

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.core.maniaplanet import callbacks as mania_callback
from pyplanet.apps.core.trackmania import callbacks as tm_callbacks

from .. import Game
from ...configuration.chess import ChessConfiguration
from ...constants import S_FORCE_LAPS_NB
from ...map_generator import MapGenerator
from ...models.chess.game_state import GameState
from ...models.chess.map_score import MapScore
from ...models.chess.piece.bishop import Bishop
from ...models.chess.piece.king import King
from ...models.chess.piece.knight import Knight
from ...models.chess.piece.pawn import Pawn
from ...models.chess.piece.queen import Queen
from ...models.chess.piece.rook import Rook
from ...models.database.chess.chess_move import ChessMove
from ...models.database.chess.chess_piece import ChessPiece
from ...models.database.chess.chess_score import ChessScore
from ...models.enums.chess_state import ChessState
from ...models.enums.game_modes import GameModes
from ...models.enums.game_script import GameScript
from ...models.enums.team import Team
from ...models.game_views.chess import ChessViews
from ...views.chess.board import ChessBoardView
from ...views.chess.ingame import ChessIngameView
from ...views.chess.settings import ChessSettingsView
from ...views.player_prompt_view import PlayerPromptView

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
        mania_callback.map.map_begin.register(self.map_begin_event)
        tm_callbacks.scores.register(self.on_race_end)


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
                self.views.ingame_view.display(),
                self.views.board_view.display()
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

        mania_callback.map.map_begin.unregister(self.map_begin_event)
        tm_callbacks.scores.unregister(self.on_race_end)

        logger.info("Back to HUB completed")

    async def map_begin_event(self, *_args, **_kwargs):
        logger.info("[map_begin_event] STARTED")
        self.game_state.current_map_completed = False
        asyncio.gather(
            self.app.map_handler.pre_load_next_map(),
            self.views.ingame_view.display(),
            self.views.board_view.hide(),
        )
        logger.info("[map_begin_event] ENDED")

    async def on_race_end(self, teams, section, *_args, **_kwargs):
        if section == "EndRound" and self.game_state.current_map_completed is False:
            self.game_state.current_map_completed = True
            team_scores = [MapScore.from_json(json) for json in teams]

            assert self.game_state.current_piece is not None
            assert self.game_state.current_piece.db is not None
            assert self.game_state.target_piece is not None
            assert self.game_state.target_piece.db is not None

            current_team = next(
                team_score
                for team_score in team_scores
                if team_score.team == self.game_state.current_piece.team
            )
            target_team = next(
                team_score
                for team_score in team_scores
                if team_score.team == self.game_state.target_piece.team
            )

            if current_team.map_points >= target_team.map_points:
                self.game_state.target_piece.captured = True
                self.game_state.target_piece.db.captured = True
                await self.game_state.target_piece.db.save()
                if isinstance(self.game_state.target_piece, King):
                    self.game_state.state = ChessState.KING_IS_DEAD
            else:
                self.game_state.current_piece.captured = True
                self.game_state.current_piece.db.captured = True
                await self.game_state.current_piece.db.save()
                if isinstance(self.game_state.current_piece, King):
                    self.game_state.state = ChessState.KING_IS_DEAD

            self.game_state.current_piece = None
            self.game_state.target_piece = None

            if self.game_state.state != ChessState.IN_PROGRESS:
                self.game_is_in_progress = False
            else:
                await self.views.board_view.display()


    async def display_piece_moves(self, player, button_id, *_args, **_kwargs):
        if any([
            not self.config.player_configs[player.login].leader,
            self.game_state.turn != Team(player.flow.team_id),
            self.game_state.current_map_completed is False,
            self.game_state.target_piece,
        ]):
            return

        x, y = map(
            int,
            button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_display_piece_moves_")[1].split("_")
        )
        piece = self.game_state.get_piece_by_coordinate(x, y)
        if piece.team != self.game_state.turn:
            return

        if self.game_state.current_piece == piece:
            self.game_state.current_piece = None
        else:
            self.game_state.current_piece = piece

        await self.views.board_view.display()

    async def move_piece(self, player, button_id, *_args, **_kwargs):
        if any([
            not self.config.player_configs[player.login].leader,
            self.game_state.turn != Team(player.flow.team_id),
            self.game_state.current_map_completed is False,
            self.game_state.target_piece,
        ]):
            return

        x, y = map(
            int,
            button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_move_piece_")[1].split("_")
        )
        promote_piece_class = None

        assert self.game_state.current_piece is not None
        assert self.game_state.current_piece.db is not None

        self.game_state.target_piece = self.game_state.get_piece_by_coordinate(x, y)
        if not self.game_state.target_piece and isinstance(self.game_state.current_piece, Pawn):
            if self.game_state.current_piece.team == Team.WHITE:
                en_passant_piece = self.game_state.get_piece_by_coordinate(x, y-1)
            elif self.game_state.current_piece.team == Team.BLACK:
                en_passant_piece = self.game_state.get_piece_by_coordinate(x, y+1)

            if isinstance(en_passant_piece, Pawn) and en_passant_piece.team != self.game_state.current_piece.team:
                self.game_state.target_piece = en_passant_piece
            elif (self.game_state.current_piece.team == Team.WHITE and y == 7) \
                or (self.game_state.current_piece.team == Team.BLACK and y == 0):
                buttons = [
                    {"name": "Queen", "value": Queen},
                    {"name": "Rook", "value": Rook},
                    {"name": "Bishop", "value": Bishop},
                    {"name": "Knight", "value": Knight},
                ]
                promote_piece_class = await PlayerPromptView.prompt_for_input(
                    player, "Promote pawn", buttons, entry=False, ok_button=False
                )

        elif not self.game_state.target_piece and isinstance(self.game_state.current_piece, King) \
            and abs(x - self.game_state.current_piece.x) == 2:
            if x - self.game_state.current_piece.x == -2:
                rook = self.game_state.get_piece_by_coordinate(self.game_state.current_piece.x - 4, y)
                rook.last_move = await ChessMove.create(
                    chess_piece=rook.db.id,
                    from_x=rook.x,
                    from_y=rook.y,
                    to_x=rook.x + 3,
                    to_y=rook.y,
                )
                rook.x += 3
            elif x - self.game_state.current_piece.x == 2:
                rook = self.game_state.get_piece_by_coordinate(self.game_state.current_piece.x + 3, y)
                rook.last_move = await ChessMove.create(
                    chess_piece=rook.db.id,
                    from_x=rook.x,
                    from_y=rook.y,
                    to_x=rook.x - 2,
                    to_y=rook.y,
                )
                rook.x -= 2

        self.game_state.current_piece.last_move = self.game_state.last_move = await ChessMove.create(
            chess_piece=self.game_state.current_piece.db.id,
            from_x=self.game_state.current_piece.x,
            from_y=self.game_state.current_piece.y,
            to_x=x,
            to_y=y,
        )

        self.game_state.current_piece.x = x
        self.game_state.current_piece.y = y

        if promote_piece_class:
            self.game_state.current_piece.captured = True
            self.game_state.current_piece.db.captured = True
            await self.game_state.current_piece.db.save()

            self.game_state.pieces.append(
                promote_piece_class(
                    self.game_state.current_piece.team,
                    self.game_state.current_piece.x,
                    self.game_state.current_piece.y,
                    await ChessPiece.create(
                        game_score=self.score.id,
                        team=self.game_state.current_piece.team.name,
                        piece=self.game_state.current_piece.__class__.__name__.lower(),
                        x=self.game_state.current_piece.x,
                        y=self.game_state.current_piece.y,
                    )
                )
            )

        if self.game_state.turn == Team.WHITE:
            self.game_state.turn = Team.BLACK
        elif self.game_state.turn == Team.BLACK:
            self.game_state.turn = Team.WHITE

        if self.game_state.target_piece:
            await self.load_map_and_display_ingame_view()
        else:
            self.game_state.current_piece = None

        await self.views.board_view.display()

        if self.game_state.state != ChessState.IN_PROGRESS:
            self.game_is_in_progress = False

    async def respawn_player(self, player: Player):
        # first, force mode 1 (spectator), then force mode 2 (player), then force mode 0 (user selectable)
        await self.app.instance.gbx('ForceSpectator', player.login, 1)
        await self.app.instance.gbx('ForceSpectator', player.login, 2)
        await self.app.instance.gbx('ForceSpectator', player.login, 0)

    # pylint: disable=duplicate-code
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
