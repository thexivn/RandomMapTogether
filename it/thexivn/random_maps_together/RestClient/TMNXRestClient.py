import logging
from typing import List

import requests
from requests import Response

from it.thexivn.random_maps_together.Data.APIMapInfo import APIMapInfo

logger = logging.getLogger(__name__)

SEARCH_PARAMS = {
    'api': 'on',
    'random': '1',
    'lengthop': '1',
    'length': '9',
    'etags': '23,46,40,41,42,37'
}


class TMNXRestClient:
    def __init__(self):
        self.base_url = "https://trackmania.exchange/mapsearch2/"
        self.search_api = "search"
        self.download_url = "https://trackmania.exchange/maps/download/"
        self._cache_request: List[APIMapInfo] = []

    def get_random_map(self) -> APIMapInfo:

        if len(self._cache_request) == 0:
            response: Response = requests.get(f'{self.base_url}{self.search_api}',
                                              params=SEARCH_PARAMS)

            results = response.json().get("results")
            for i in range(0, 100):
                _map = results[i]
                self._cache_request.add(APIMapInfo(_map.get("TrackUID"), int(_map.get('AuthorTime')), None))

        next_map = self._cache_request.pop()
        next_map.content = self.map_map_content(next_map.uuid)
        return next_map

    def map_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_url, map_id)
        content = requests.get(f'{self.download_url}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content
