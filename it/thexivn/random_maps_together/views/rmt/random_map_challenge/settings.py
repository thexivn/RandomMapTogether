import logging
from ..settings import RandomMapsTogetherSettingsView

logger = logging.getLogger(__name__)

class RandomMapChallengeSettingsView(RandomMapsTogetherSettingsView):
    widget_x = -100
    widget_y = 73.5
    z_index = 5
    size_x = 66
    size_y = 9

    template_name = "random_maps_together/rmt/random_map_challenge/settings.xml"
