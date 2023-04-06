from enum import Enum
import logging
import requests
from ..Data.APIMapInfo import APIMapInfo
from ..Data.map_tag import MapTag

logger = logging.getLogger(__name__)

class MapGeneratorType(Enum):
    RANDOM = "RANDOM"
    TOTD = "TOTD"
    CUSTOM = "CUSTOM"

class TMExchangeURLS(Enum):
    MAP_SEARCH = "https://trackmania.exchange/mapsearch2/search/"
    MAPPACK_SEARCH = "https://trackmania.exchange/mappacksearch/search/"
    GET_MAP_INFO_BY_ID = f"https://trackmania.exchange/api/maps/get_map_info/id/"
    GET_MAP_PACK_INFO_BY_ID = f"https://trackmania.exchange/api/mappack/get_info/"
    GET_TAGS = f"https://trackmania.exchange/api/tags/gettags/"
    GET_MAPPACK_TRACKS = "https://trackmania.exchange/api/mappack/get_mappack_tracks/"
    DOWNLOAD_MAP = "https://trackmania.exchange/maps/download/"

class MapGenerator:
    def __init__(self, app):
        self.map_generator_type = MapGeneratorType.RANDOM
        self.app = app
        self.played_maps = []
        self.map_tags = self.get_map_tags()

    def get_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", TMExchangeURLS.DOWNLOAD_MAP.value, map_id)
        content = self.app.session.get(f'{TMExchangeURLS.DOWNLOAD_MAP.value}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content

    def get_map_tags(self):
        return [MapTag(**tag) for tag in self.app.session.get(TMExchangeURLS.GET_TAGS.value).json()]

    def get_map(self):
        return self.get_random_map()

    def get_random_map(self) -> APIMapInfo:
        response = requests.get(
            f'{TMExchangeURLS.MAP_SEARCH.value}',
            params={
                'api': 'on',
                'random': '1',
                'lengthop': '1',
                'length': '9',
                'etags': '23,46,40,41,42,37'
            }
        )

        first_map = response.json().get("results")[0]
        return APIMapInfo.from_json(first_map, self.map_tags)
