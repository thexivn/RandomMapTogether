import logging

from pyplanet.views.generics.widget import WidgetView
from ...configuration.rmt.rmc_configuration import RandomMapChallengeConfiguration
# pylint: disable=duplicate-code
logger = logging.getLogger(__name__)

class ChessSettingsView(WidgetView):
    widget_x = -100
    widget_y = 73.5
    z_index = 5
    size_x = 66
    size_y = 9

    template_name = "random_maps_together/chess/settings.xml"

    def __init__(self, app, config):
        super().__init__()
        logger.info("Loading VIEW")
        self.id = "it_thexivn_RandomMapsTogether_settings"
        self.app = app
        self.manager = app.context.ui
        self.config = config
        self.subscribe("ui_start", self.app.start_game)

        self.subscribe("ui_set_map_generator_random", self.config.set_map_generator)
        self.subscribe("ui_set_map_generator_totd", self.config.set_map_generator)
        self.subscribe("ui_set_map_generator_map_pack", self.config.set_map_generator)

        self.subscribe("ui_display_player_settings", self.config.display_player_settings)
        self.subscribe("ui_display_leaderboard", self.config.display_leaderboard)

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["config"] = self.config

        return data
