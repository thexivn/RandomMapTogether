import logging
from datetime import datetime
from typing import List

import aiohttp

from ..Data.APIMapInfo import APIMapInfo

logger = logging.getLogger(__name__)


def get_session():
    return aiohttp.ClientSession(headers={
        'User-Agent': f'app=RMT++ (PyPlanet) / contact=@XertroV,rmt@xk.io'
    })



SEARCH_PARAMS = {
    'api': 'on',
    'random': '1',
    'lengthop': '1',
    'length': '9',
    'etags': '23,46,40,41,42,37'
}

SEARCH_PARAMS_STR = '&'.join([f"{k}={v}" for k,v in SEARCH_PARAMS.items()])


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
        self.search_api = "search"
        self.download_url = "https://trackmania.exchange/maps/download/"

    async def get_random_map(self) -> APIMapInfo:
        async with get_session() as session:
            async with await session.get(f'{self.base_url}{self.search_api}?{SEARCH_PARAMS_STR}') as resp:
                if resp.status >= 400:
                    logging.warn(f"Err getting random map: {resp.status}, {await resp.content.read()}")
                    return
                j = await resp.json()
                first_map = j.get("results")[0]
                return APIMapInfo(
                    first_map.get("TrackUID"),
                    int(first_map.get('AuthorTime')),
                    _fix_datetime(first_map.get("UpdatedAt")).date(),
                    await self.get_map_content(first_map.get("TrackID")),
                    _get_tags(first_map.get("Tags")))

    async def get_map_content(self, map_id) -> bytes:
        logger.info("downloading %s%s", self.download_url, map_id)
        async with get_session() as session:
            async with await session.get(f'{self.download_url}{map_id}') as resp:
                if resp.status >= 400:
                    logging.warn(f"Err getting map content: {resp.status}, {await resp.content.read()}")
                    return
                logger.info("download completed for mapID %s", map_id)
                return await resp.content.read()
