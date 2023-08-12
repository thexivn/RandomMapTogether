import logging
from ..settings import RandomMapsTogetherSettingsView
from ....configuration.rmt.rms_configuration import RandomMapSurvivalConfiguration

logger = logging.getLogger(__name__)

class RandomMapChallengeSettingsView(RandomMapsTogetherSettingsView):
    template_name = "random_maps_together/rmt/random_map_challenge/settings.xml"

    def __init__(self, app, config: RandomMapSurvivalConfiguration):
        super().__init__(app, config)
        self.subscribe("ui_toggle_infinite_skips", self.config.toggle_infinite_skips)
