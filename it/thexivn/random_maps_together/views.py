import logging

from pyplanet.views.generics.widget import TimesWidgetView

logger = logging.getLogger(__name__)


class RandomMapsTogetherView(TimesWidgetView):
    widget_x = -120
    widget_y = 80
    z_index = 200
    size_x = 70
    size_y = 20
    title = "Random Maps Together"

    template_name = "random_maps_together/widget.xml"

    def __init__(self, app):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_widget"

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()
        data["time_left"] = "1:00:00"
        return data
