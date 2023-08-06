import logging

from pyplanet.views import TemplateView

from ...models.database.chess.chess_score import ChessScore
from ...models.database.chess.chess_move import ChessMove
from ...models.enums.team import Team

logger = logging.getLogger(__name__)

class ChessBoardView(TemplateView):
    template_name = "random_maps_together/chess/board.xml"

    def __init__(self, game):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.game = game
        self.manager = game.app.context.ui
        self.game_score: ChessScore
        self.id = "it_thexivn_RandomMapsTogether_scoreboard"
        self.subscribe("ui_hide_board", self.hide)
        for x in range(8):
            for y in range(8):
                self.subscribe(f"ui_display_piece_moves_{x}_{y}", self.display_piece_moves)
                self.subscribe(f"ui_move_piece_{x}_{y}", self.move_piece)

    async def get_context_data(self):
        data = await super().get_context_data()
        data["pieces"] = self.game.game_state.pieces_in_play
        data["moves"] = self.game.game_state.get_moves_for_piece(self.game.game_state.current_piece)
        return data

    async def display(self, player=None, *_args):
        if player:
            await super().display([player.login])
        else:
            await super().display()

    async def hide(self, player=None, *_args):
        if player:
            await super().hide([player.login])
        else:
            await super().hide()

    async def display_piece_moves(self, player, button_id, _values):
        if not self.game.config.player_configs[player.login].leader:
            return

        if self.game.game_state.turn != Team(player.flow.team_id):
            return

        x, y = map(int, button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_display_piece_moves_")[1].split("_"))
        piece = self.game.game_state.get_piece_by_coordinate(x, y)
        if piece.team != Team(player.flow.team_id):
            return

        if self.game.game_state.current_piece == piece:
            self.game.game_state.current_piece = None
        else:
            self.game.game_state.current_piece = piece

        await self.display(player)

    async def move_piece(self, player, button_id, _values):
        if not self.game.config.player_configs[player.login].leader:
            return

        if self.game.game_state.turn != Team(player.flow.team_id):
            return

        x, y = map(int, button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_move_piece_")[1].split("_"))
        target_piece = self.game.game_state.get_piece_by_coordinate(x, y)
        if target_piece and target_piece.team != self.game.game_state.current_piece.team:
            target_piece.captured = True
            target_piece.db.captured = True

        logger.info(self.game.game_state.current_piece.db)
        await ChessMove.create(
            chess_piece=self.game.game_state.current_piece.db.id,
            from_x=self.game.game_state.current_piece.x,
            from_y=self.game.game_state.current_piece.y,
            to_x=x,
            to_y=y,
        )

        self.game.game_state.current_piece.x = x
        self.game.game_state.current_piece.y = y

        # if self.game.game_state.turn == Team.WHITE:
        #     self.game.game_state.turn == Team.BLACK
        # elif self.game.game_state.turn == Team.BLACK:
        #     self.game.game_state.turn == Team.WHITE

        self.game.game_state.current_piece = None
        await self.display(player)
