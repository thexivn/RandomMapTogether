from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MapGeneratorType(Enum):
    RANDOM = "RANDOM"
    TOTD = "TOTD"
    CUSTOM = "CUSTOM"

class MapGenerator:
    def __init__(self, app):
        self.map_generator_type = MapGeneratorType.RANDOM
        self.app = app
        self.played_maps = set()

    async def get_map(self):
        return await self.app.tmx_client.search_random_map()
