import logging

import random
from typing import Set

from ..Data.APIMapInfo import APIMapInfo
from . import MapGenerator, MapGeneratorType, TMExchangeURLS

logger = logging.getLogger(__name__)


class Custom(MapGenerator):
    def __init__(self, app):
        super().__init__(app)
        self.map_generator_type = MapGeneratorType.CUSTOM
        self.maps: Set[APIMapInfo] = set()

    def add_map(self, map_id):
        response = self.app.session.get(f"{TMExchangeURLS.GET_MAP_INFO_BY_ID.value}{map_id}").json()
        self.maps.add(APIMapInfo.from_json(response, self.map_tags))

    def add_map_pack(self, map_id):
        response = self.app.session.get(f"{TMExchangeURLS.GET_MAPPACK_TRACKS.value}{map_id}").json()
        for map in response:
            self.maps.add(APIMapInfo.from_json(map, self.map_tags))

    def remove_map(self, map_id):
        self.maps.remove(next(map for map in self.maps if map.TrackID == map_id))

    def get_map(self) -> APIMapInfo:
        non_played_maps = [map for map in self.maps if map.TrackUID not in self.played_maps]
        if non_played_maps:
            return random.choice(non_played_maps)
        else:
            return self.get_random_map()

    def map_pack_id_validator(self, map_pack_id):
        response_json = self.app.session.get(f"{TMExchangeURLS.GET_MAP_PACK_INFO_BY_ID.value}{map_pack_id}").json()
        if response_json.get("Message", "") == "Mappack does not exist.":
            raise ValueError(f"Mappack does not exist: {map_pack_id}")

    def map_id_validator(self, map_id):
        try:
            self.app.session.get(f"{TMExchangeURLS.GET_MAP_INFO_BY_ID.value}{map_id}").json()
        except Exception:
            raise ValueError(f"Map ID does not exist: {map_id}")
