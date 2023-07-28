import logging
from pyplanet.views.generics.widget import WidgetView

from ...models.enums.medal_urls import MedalURLs
# pylint: disable=duplicate-code
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
        self.subscribe("ui_skip_medal", self.game.command_skip_medal)
        self.subscribe("ui_skip", self.game.command_skip)
        self.subscribe("ui_toggle_pause", self.game.command_toggle_pause)
        self.subscribe("ui_display_player_settings", self.game.config.display_player_settings)
        self.subscribe("ui_display_scoreboard", self.game.views.board_view.display_scoreboard_for_player)

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["game"] = self.game

        data["total_goal_medals"] = self.game.score.total_goal_medals
        data["total_skip_medals"] = self.game.score.total_skip_medals

        data["is_paused"] = self.game.game_state.is_paused
        data["goal_medal_url"] = MedalURLs[self.game.config.goal_medal.name].value
        data["skip_medal_url"] = MedalURLs[self.game.config.skip_medal.name].value
        data["game_started"] = self.game.game_is_in_progress
        data["skip_medal"] = self.game.game_state.skip_medal
        data["skip_pre_patch_ice_visible"] = self.game.app.map_handler.pre_patch_ice
        data["map_loading"] = self.game.app.map_handler.map_is_loading

        return data
