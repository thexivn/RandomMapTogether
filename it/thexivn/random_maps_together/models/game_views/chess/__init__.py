from dataclasses import dataclass, field

from .. import GameViews
from ....views.chess.settings import ChessSettingsView
from ....views.chess.ingame import ChessIngameView
from ....views.chess.board import ChessBoardView

@dataclass
class ChessViews(GameViews):
    settings_view: ChessSettingsView = field(init=False)
    ingame_view: ChessIngameView = field(init=False)
    board_view: ChessBoardView = field(init=False)
