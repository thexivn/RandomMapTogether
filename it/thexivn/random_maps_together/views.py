import logging

from pyplanet.views.generics.widget import TimesWidgetView

from it.thexivn.random_maps_together.Data.GameScore import GameScore

logger = logging.getLogger(__name__)


class RandomMapsTogetherView(TimesWidgetView):
    widget_x = -140
    widget_y = 85
    z_index = 5
    size_x = 70
    size_y = 10
    title = "Random Maps Together"

    template_name = "random_maps_together/widget.xml"

    def __init__(self, app):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_widget"
        self._score = None
        self.ui_tools_enabled = True
        self.game_started = False

    def set_score(self, score: GameScore):
        self._score = score

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()
        if self._score:
            data["AT"] = self._score.total_at
            data["GOLD"] = self._score.total_gold
        else:
            data["AT"] = 0
            data["GOLD"] = 0

        data["ui_tools_enabled"] = self.ui_tools_enabled
        data["game_started"] = self.game_started

        return data
