import logging

from pyplanet.views import TemplateView

from ...models.database.chess.chess_score import ChessScore
from ...models.database.chess.chess_move import ChessMove
from ...models.chess.piece.pawn import Pawn
from ...models.chess.piece.king import King
from ...models.chess.piece.queen import Queen
from ...models.chess.piece.rook import Rook
from ...models.chess.piece.bishop import Bishop
from ...models.chess.piece.knight import Knight
from ...models.database.chess.chess_piece import ChessPiece
from ...models.enums.team import Team
from ...models.enums.chess_state import ChessState
from ..player_prompt_view import PlayerPromptView

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
        data["moves"] = await self.game.game_state.get_moves_for_piece(self.game.game_state.current_piece)
        if not data["moves"]:
            self.game.game_state.current_piece = None
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
        # if not self.game.config.player_configs[player.login].leader:
        #     return

        # if self.game.game_state.turn != Team(player.flow.team_id):
        #     return

        x, y = map(int, button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_display_piece_moves_")[1].split("_"))
        piece = await self.game.game_state.get_piece_by_coordinate(x, y)
        if piece.team != self.game.game_state.turn:
            return

        if self.game.game_state.current_piece == piece:
            self.game.game_state.current_piece = None
        else:
            self.game.game_state.current_piece = piece

        await self.display(player)

    async def move_piece(self, player, button_id, _values):
        # if not self.game.config.player_configs[player.login].leader:
        #     return

        # if self.game.game_state.turn != Team(player.flow.team_id):
        #     return

        x, y = map(int, button_id.split("it_thexivn_RandomMapsTogether_scoreboard__ui_move_piece_")[1].split("_"))
        promote_piece_class = None

        target_piece = await self.game.game_state.get_piece_by_coordinate(x, y)
        if target_piece and target_piece.team != self.game.game_state.current_piece.team:
            target_piece.captured = True
            target_piece.db.captured = True
        elif not target_piece and isinstance(self.game.game_state.current_piece, Pawn):
            if self.game.game_state.current_piece.team == Team.WHITE:
                en_passant_piece = await self.game.game_state.get_piece_by_coordinate(x, y-1)
            elif self.game.game_state.current_piece.team == Team.BLACK:
                en_passant_piece = await self.game.game_state.get_piece_by_coordinate(x, y+1)

            if en_passant_piece and isinstance(en_passant_piece, Pawn) and en_passant_piece.team != self.game.game_state.current_piece.team:
                en_passant_piece.captured = True
                en_passant_piece.db.captured = True
            elif (self.game.game_state.current_piece.team == Team.WHITE and y == 7) or (self.game.game_state.current_piece.team == Team.BLACK and y == 0):
                buttons = [
                    {"name": "Queen", "value": Queen},
                    {"name": "Rook", "value": Rook},
                    {"name": "Bishop", "value": Bishop},
                    {"name": "Knight", "value": Knight},
                ]
                promote_piece_class = await PlayerPromptView.prompt_for_input(player, "Promote pawn", buttons, entry=False)

        elif not target_piece and isinstance(self.game.game_state.current_piece, King) and abs(x - self.game.game_state.current_piece.x) == 2:
            if x - self.game.game_state.current_piece.x == -2:
                rook = await self.game.game_state.get_piece_by_coordinate(self.game.game_state.current_piece.x - 4, y)
                await ChessMove.create(
                    chess_piece=rook.db.id,
                    from_x=rook.x,
                    from_y=rook.y,
                    to_x=rook.x + 3,
                    to_y=rook.y,
                )
                rook.x += 3
            elif x - self.game.game_state.current_piece.x == 2:
                rook = await self.game.game_state.get_piece_by_coordinate(self.game.game_state.current_piece.x + 3, y)
                await ChessMove.create(
                    chess_piece=rook.db.id,
                    from_x=rook.x,
                    from_y=rook.y,
                    to_x=rook.x - 2,
                    to_y=rook.y,
                )
                rook.x -= 2
        await ChessMove.create(
            chess_piece=self.game.game_state.current_piece.db.id,
            from_x=self.game.game_state.current_piece.x,
            from_y=self.game.game_state.current_piece.y,
            to_x=x,
            to_y=y,
        )

        self.game.game_state.current_piece.x = x
        self.game.game_state.current_piece.y = y

        if promote_piece_class:
            self.game.game_state.current_piece.captured = True
            new_piece = promote_piece_class(
                self.game.game_state.current_piece.team,
                self.game.game_state.current_piece.x,
                self.game.game_state.current_piece.y,
            )

            new_piece.db, _ = await ChessPiece.get_or_create(
                game_score=self.game.score.id,
                team=self.game.game_state.current_piece.team.name,
                piece=self.game.game_state.current_piece.__class__.__name__.lower(),
                x=self.game.game_state.current_piece.x,
                y=self.game.game_state.current_piece.y,
            )
            self.game.game_state.pieces.append(new_piece)

        if self.game.game_state.turn == Team.WHITE:
            self.game.game_state.turn = Team.BLACK
        elif self.game.game_state.turn == Team.BLACK:
            self.game.game_state.turn = Team.WHITE

        available_moves_for_new_team = [
            move
            for piece in self.game.game_state.current_pieces
            for move in await self.game.game_state.get_moves_for_piece(piece)
        ]
        pieces_attacking_king = await self.game.game_state.get_enemy_pieces_attacking_coordinate(self.game.game_state.current_king.x, self.game.game_state.current_king.y)
        if not available_moves_for_new_team and pieces_attacking_king:
            self.game.game_state.state = ChessState.CHECKMATE
            self.game.game_is_in_progress = False
        elif not available_moves_for_new_team and not pieces_attacking_king:
            self.game.game_state.state = ChessState.STALEMATE
            self.game.game_is_in_progress = False

        self.game.game_state.current_piece = None
        await self.display(player)
