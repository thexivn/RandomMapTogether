from enum import Enum
import logging
import requests
from ..Data.APIMapInfo import APIMapInfo

logger = logging.getLogger(__name__)

class MapGeneratorType(Enum):
    RANDOM = "RANDOM"
    TOTD = "TOTD"
    MAP_PACK = "MAP PACK"

class MapGenerator:
    def __init__(self, app):
        self.map_generator_type = MapGeneratorType.RANDOM
        self.app = app
        self.search_url = "https://trackmania.exchange/mapsearch2/search/"
        self.download_url = "https://trackmania.exchange/maps/download/"
        self.map_pack_url = "https://trackmania.exchange/api/mappack/get_mappack_tracks/"
        self.search_map_packs_url = "https://trackmania.exchange/mappacksearch/search/"
        self.played_maps = []

    def get_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_url, map_id)
        content = self.app.session.get(f'{self.download_url}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content

    def get_map(self):
        return self.get_random_map()

    def get_random_map(self) -> APIMapInfo:
        response = requests.get(
            f'{self.search_url}',
            params={
                'api': 'on',
                'random': '1',
                'lengthop': '1',
                'length': '9',
                'etags': '23,46,40,41,42,37'
            }
        )

        first_map = response.json().get("results")[0]
        return APIMapInfo(
            first_map.get("TrackUID"),
            int(first_map.get('AuthorTime')),
            first_map.get("UpdatedAt"),
            self.get_map_content(first_map.get("TrackID")),
            first_map.get("Tags")
        )
