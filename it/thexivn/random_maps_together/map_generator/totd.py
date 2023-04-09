import logging
import random

from ..models.api_response.api_map_info import APIMapInfo
from . import MapGenerator, MapGeneratorType

logger = logging.getLogger(__name__)


class TOTD(MapGenerator):
    def __init__(self, app):
        super().__init__(app)
        self.map_generator_type = MapGeneratorType.TOTD

    async def get_map(self) -> APIMapInfo:
        map_pack = await self.app.tmx_client.search_random_mappack_totd()
        map_pack_tracks = await self.app.tmx_client.get_mappack_tracks(map_pack.id)
        return random.choice([map for map in map_pack_tracks if map not in self.played_maps])
