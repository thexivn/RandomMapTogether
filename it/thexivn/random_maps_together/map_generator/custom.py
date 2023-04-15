import logging

import random
from typing import Set


from . import MapGenerator, MapGeneratorType
from ..models.api_response.api_map_info import APIMapInfo
from ..views.custom_maps_view import CustomMapsView

logger = logging.getLogger(__name__)


class Custom(MapGenerator):
    def __init__(self, app):
        super().__init__(app)
        self.map_generator_type = MapGeneratorType.CUSTOM
        self.maps: Set[APIMapInfo] = set()
        self.maps_ui = CustomMapsView(app)

    async def add_map(self, map_id):
        self.maps.add(await self.app.tmx_client.get_map_info_by_id(map_id))

    async def add_map_pack(self, map_pack_id):
        self.maps.update(await self.app.tmx_client.get_mappack_tracks(map_pack_id))

    async def remove_map(self, map_id):
        self.maps.remove(next(map for map in self.maps if map.TrackID == map_id))

    async def get_map(self) -> APIMapInfo:
        non_played_maps = [map for map in self.maps if map not in self.played_maps]
        if non_played_maps:
            return random.choice(non_played_maps)
        else:
            return await self.get_random_map()

    async def map_pack_id_validator(self, map_pack_id):
        try:
            await self.app.tmx_client.get_mappack_info_by_id(map_pack_id)
        except Exception:
            raise ValueError(f"Mappack does not exist: {map_pack_id}")

    async def map_id_validator(self, map_id):
        try:
            await self.app.tmx_client.get_map_info_by_id(map_id)
        except Exception:
            raise ValueError(f"Map ID does not exist: {map_id}")
