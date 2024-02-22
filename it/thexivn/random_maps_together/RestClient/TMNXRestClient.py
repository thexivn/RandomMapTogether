import logging
from datetime import datetime
from typing import List

import requests
from requests import Response

from apps.it.thexivn.random_maps_together.Data.APIMapInfo import APIMapInfo

logger = logging.getLogger(__name__)



def _get_tags(tags_str: str) -> List[int]:
    return [int(tag) for tag in tags_str.split(',')]


def _fix_datetime(dtime: str) -> datetime:
    count = len(dtime.split('.')[-1])
    if count < 3:
        dtime += '0' * (3 - count)

    return datetime.fromisoformat(dtime)


class TMNXRestClient:
    def __init__(self):
        self.base_url = "https://trackmania.exchange/mapsearch2/"
        self.mirror_url = "https://map-monitor.xk.io/mapsearch2/"
        self.search_api = "search"
        self.download_url = "https://trackmania.exchange/maps/download/"
        self.download_mirror = "https://map-monitor.xk.io/maps/download/"
        self.headers = {'user-agent': 'pyplanet-rmt/1.0.0'}
        self.tags = '5'


    def get_random_map(self, tags=None) -> APIMapInfo:
        params = {
            'api': 'on',
            'random': '1',
            'lengthop': '3',    # 1
            'length': '4',      # 9
            'mtype': 'TM_Race',
            'etags': '6,8,10,23,24,30,31,37,40,45,46,47'
        }

        if tags != " ":
            params.update({"tags": tags})

        response: Response = requests.get(f'{self.base_url}{self.search_api}', params=params)
        if response.status_code == 200:
            first_map = response.json().get("results")[0]
            return APIMapInfo(
                first_map.get("TrackUID"),
                int(first_map.get('AuthorTime')),
                _fix_datetime(first_map.get("UpdatedAt")).date(),
                self.map_map_content(first_map.get("TrackID")),
                _get_tags(first_map.get("Tags")))
        else:
            response: Response = requests.get(f'{self.mirror_url}{self.search_api}', params=params,
                                              headers=self.headers)
            first_map = response.json().get("results")[0]
            return APIMapInfo(
                first_map.get("TrackUID"),
                int(first_map.get('AuthorTime')),
                _fix_datetime(first_map.get("UpdatedAt")).date(),
                self.map_mirror_content(first_map.get("TrackID")),
                _get_tags(first_map.get("Tags")))

    def map_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_url, map_id)
        content = requests.get(f'{self.download_url}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content

    def map_mirror_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_mirror, map_id)
        content = requests.get(f'{self.download_mirror}{map_id}').content
        logger.info("download completed for mapID %s", map_id)
        return content
