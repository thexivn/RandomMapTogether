import logging
import requests

logger = logging.getLogger(__name__)


class TMNXRestClient:
    def __init__(self):
        self.base_url = "https://trackmania.exchange/mapsearch2/"
        self.search_api = "search"
        self.download_url = "https://trackmania.exchange/maps/download/"

    def get_random_map(self):
        response = requests.get(f'{self.base_url}{self.search_api}',
                                params={'api': 'on', 'random':'1', 'lengthop': '1', 'length': '9'})

        map = response.json().get("results")[0]

        return {
            'uuid': map.get("TrackUID"),
            'author_time': int(map.get('AuthorTime')),
            'content': self.map_map_content(map.get("TrackID"))
        }

    def map_map_content(self, map_id):
        logger.info("downloading %s%s", self.download_url,map_id)
        content = requests.get(f'{self.download_url}{map_id}').content
        logger.info(len(content))
        return content
