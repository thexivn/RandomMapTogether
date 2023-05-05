import logging
from ..settings import RandomMapsTogetherSettingsView

logger = logging.getLogger(__name__)

class RandomMapChallengeSettingsView(RandomMapsTogetherSettingsView):
    template_name = "random_maps_together/rmt/random_map_challenge/settings.xml"
