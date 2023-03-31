import logging

import requests
import random

from ..Data.APIMapInfo import APIMapInfo
from . import MapGenerator

logger = logging.getLogger(__name__)


class MapPack(MapGenerator):
    def __init__(self, map_pack_id=None):
        super().__init__()
        self.map_pack_id = map_pack_id

    def get_map(self) -> APIMapInfo:
        response = requests.get(f"{self.map_pack_url}{self.map_pack_id}").json()
        non_played_maps = [map for map in response if map.get("TrackUID") not in self.played_maps]
        if non_played_maps:
            map = random.choice(non_played_maps)

            return APIMapInfo(
                map.get("TrackUID"),
                int(map.get('AuthorTime')),
                map.get("UpdatedAt"),
                self.get_map_content(map.get("TrackID")),
                map.get("Tags")
            )
        else:
            return self.get_random_map()
