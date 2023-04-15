import logging


from ..ingame import RandomMapsTogetherIngameView
from ....models.enums.game_modes import GameModes

logger = logging.getLogger(__name__)


class RandomMapChallengeIngameView(RandomMapsTogetherIngameView):
    title = GameModes.RANDOM_MAP_CHALLENGE.value

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()
        data["free_skip_visible"] = self.game._game_state.free_skip_available or self.game.config.infinite_free_skips
        return data
