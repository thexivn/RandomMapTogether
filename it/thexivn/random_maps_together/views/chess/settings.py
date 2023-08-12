import logging

from ..settings import SettingsView

logger = logging.getLogger(__name__)

class ChessSettingsView(SettingsView):
    template_name = "random_maps_together/chess/settings.xml"

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["config"] = self.config

        return data
