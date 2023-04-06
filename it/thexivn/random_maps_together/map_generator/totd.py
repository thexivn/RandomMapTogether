import logging
import random

from ..Data.APIMapInfo import APIMapInfo
from . import MapGenerator, MapGeneratorType, TMExchangeURLS

logger = logging.getLogger(__name__)


class TOTD(MapGenerator):
    def __init__(self, app):
        super().__init__(app)
        self.map_generator_type = MapGeneratorType.TOTD

    def get_map(self) -> APIMapInfo:
        response = self.app.session.get(
            f'{TMExchangeURLS.MAPPACK_SEARCH.value}',
            params={
                "api": "on",
                "random": 1,
                "mode": 1,
                "creatorid": 21,
                "name": "TOTD - Track of the Day",
            }
        )
        map_pack = response.json().get("results")[0]
        map_pack_maps = self.app.session.get(f"{TMExchangeURLS.GET_MAPPACK_TRACKS.value}{map_pack.get('ID')}").json()
        map = random.choice([map for map in map_pack_maps if map.get("TrackUID") not in self.played_maps])
        return APIMapInfo.from_json(map, self.map_tags)
