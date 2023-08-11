import logging
from pyplanet.views.generics.widget import WidgetView

logger = logging.getLogger(__name__)

class ChessIngameView(WidgetView):
    widget_x = -100
    widget_y = 86
    z_index = 5
    size_x = 66
    size_y = 9

    template_name = "random_maps_together/chess/ingame.xml"

    def __init__(self, game):
        super().__init__()
        logger.info("Loading VIEW")
        self.id = "it_thexivn_RandomMapsTogether_ingame"
        self.game = game
        self.manager = game.app.context.ui

        self.subscribe("ui_stop", self.game.app.stop_game)
        self.subscribe("ui_display_player_settings", self.game.config.display_player_settings)
        self.subscribe("ui_display_board", self.game.views.board_view.display)

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["game_started"] = self.game.game_is_in_progress
        data["map_loading"] = self.game.app.map_handler.map_is_loading

        return data
