import logging
import asyncio
from typing import Optional

from pyplanet.apps.core.maniaplanet.models import Player
from pyplanet.apps.config import AppConfig
from ..models.game_views import GameViews
from ..models.enums.game_modes import GameModes

logger = logging.getLogger(__name__)

class Game:
    def __init__(self, app: AppConfig):
        self.app = app
        self.game_mode: GameModes
        self.game_starting_player: Optional[Player] = None
        self.game_is_in_progress: bool = False
        self.views: Optional[GameViews] = None

    async def player_connect(self, player: Player, is_spectator: bool, source, *args, **kwargs):
        pass

    async def player_disconnect(self, player: Player, reason: str, source, *args, **kwargs):
        pass

    async def load_map_and_display_ingame_view(self):
        try:
            await asyncio.gather(
                self.app.map_handler.load_with_retry(),
                self.views.ingame_view.display()
            )
        except Exception as exc:
            await asyncio.gather(
                self.views.ingame_view.hide(),
                self.app.game.views.settings_view.display()
            )
            raise RuntimeError(f"Error occurred when loading next map: {str(exc)}") from exc
