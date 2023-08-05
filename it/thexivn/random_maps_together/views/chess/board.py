import logging

from pyplanet.views import TemplateView

from ...models.database.chess.chess_score import ChessScore
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
        data["white_moves"] = self.game.game_state.white_current_moves
        data["black_moves"] = self.game.game_state.black_current_moves
        return data

    async def display(self, player=None, *_args):
        if player:
            await super().display([player.login])
        else:
            super().display()

    async def hide(self, player=None, *_args):
        if player:
            await super().hide([player.login])
        else:
            super().display()

    async def display_piece_moves(self, player, button_id, _values):
        x, y = button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_display_piece_moves_")[1].split("_")
        piece = self.game.game_state.get_piece_by_coordinate(int(x), int(y))
        if player.flow.team_id == 0 and self.game.game_state.turn == Team.WHITE:
            if self.game.game_state.white_current_piece == piece:
                self.game.game_state.white_current_piece = None
                self.game.game_state.white_current_moves = []
            elif piece.team == Team.WHITE:
                self.game.game_state.white_current_piece = piece
                self.game.game_state.white_current_moves = self.game.game_state.get_moves_for_piece(piece)

        elif player.flow.team_id == 1 and self.game.game_state.turn == Team.BLACK:
            if self.game.game_state.black_current_piece == piece:
                self.game.game_state.black_current_piece = None
                self.game.game_state.black_current_moves = []
            elif piece.team == Team.BLACK:
                self.game.game_state.black_current_piece = piece
                self.game.game_state.black_current_moves = self.game.game_state.get_moves_for_piece(piece)
        await self.display(player)

    async def move_piece(self, player, button_id, _values):
        x, y = map(int, button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_move_piece_")[1].split("_"))
        target_piece = self.game.game_state.get_piece_by_coordinate(x, y)
        if player.flow.team_id == 0:
            piece = self.game.game_state.white_current_piece
            self.game.game_state.white_current_moves.clear()
            self.game.game_state.white_current_piece = None
            if target_piece and target_piece.team == Team.BLACK:
                target_piece.captured = True
            # self.game.game_state.turn = Team.BLACK
        elif player.flow.team_id == 1:
            piece = self.game.game_state.black_current_piece
            self.game.game_state.black_current_moves.clear()
            self.game.game_state.black_current_piece = None
            if target_piece and target_piece.team != Team.WHITE:
                target_piece.captured = True
            # self.game.game_state.turn = Team.WHITE

        piece.x = x
        piece.y = y

        await self.display(player)
