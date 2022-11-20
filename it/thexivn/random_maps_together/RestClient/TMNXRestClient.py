import logging
import requests

from it.thexivn.random_maps_together.Data.APIMapInfo import APIMapInfo

logger = logging.getLogger(__name__)


class TMNXRestClient:
    def __init__(self):
        self.base_url = "https://trackmania.exchange/mapsearch2/"
        self.search_api = "search"
        self.download_url = "https://trackmania.exchange/maps/download/"

    def get_random_map(self) -> APIMapInfo:
        response = requests.get(f'{self.base_url}{self.search_api}',
                                params={'api': 'on', 'random':'1', 'lengthop': '1', 'length': '9'})

        first_map = response.json().get("results")[0]
        return APIMapInfo(first_map.get("TrackUID"), int(first_map.get('AuthorTime')),
                          self.map_map_content(first_map.get("TrackID")))

    def map_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_url,map_id)
        content = requests.get(f'{self.download_url}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content
