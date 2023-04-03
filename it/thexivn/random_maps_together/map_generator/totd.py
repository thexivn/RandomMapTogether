import logging
import random

from ..Data.APIMapInfo import APIMapInfo
from . import MapGenerator

logger = logging.getLogger(__name__)


class TOTD(MapGenerator):
    def get_map(self) -> APIMapInfo:
        response = self.app.session.get(
            f'{self.search_map_packs_url}',
            params={
                "api": "on",
                "random": 1,
                "mode": 1,
                "creatorid": 21,
                "name": "TOTD - Track of the Day",
            }
        )
        map_pack = response.json().get("results")[0]
        map_pack_maps = self.app.session.get(f"{self.map_pack_url}{map_pack.get('ID')}").json()
        map = random.choice([map for map in map_pack_maps if map.get("TrackUID") not in self.played_maps])

        return APIMapInfo(
            map.get("TrackUID"),
            int(map.get('AuthorTime')),
            map.get("UpdatedAt"),
            self.get_map_content(map.get("TrackID")),
            map.get("Tags")
        )
