import io
import logging

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager

from it.thexivn.random_maps_together.RestClient.TMNXRestClient import TMNXRestClient

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, map_manager: MapManager):
        self.tmnx_rest_client = TMNXRestClient()
        self.hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self.hub_id = '63710'
        self.map_manager = map_manager
        self.loaded_map = None
        self.event_map: Map = None

    async def load_next_map(self):
        logger.info("Trying to load next map ...")
        self.loaded_map = self.tmnx_rest_client.get_random_map()
        map_to_remove = self.map_manager.current_map
        logger.info(f'{self.loaded_map.get("uuid")}.Map.Gbx')
        await self.map_manager.upload_map(io.BytesIO(self.loaded_map.get("content")),
                                          f'{self.loaded_map.get("uuid")}.Map.Gbx', overwrite=True)
        await self.map_manager.update_list(True, True)
        logger.info("uploaded next map...")
        await self.map_manager.set_current_map(self.loaded_map.get("uuid"))
        await self.map_manager.remove_map(map_to_remove, True)
        logger.info("map loaded")

    async def load_hub(self):
        logger.info("loading HUB map ...")
        content = self.tmnx_rest_client.map_map_content(self.hub_id)
        try:
            await self.map_manager.upload_map(io.BytesIO(content), f'{self.hub_id}.Map.Gbx', overwrite=True)
            await self.map_manager.update_list(True, True)
            await self.map_manager.set_current_map(self.hub_map)
        except:
            pass

        logger.info("hub map loaded")

    async def remove_loaded_map(self):
        try:
            await self.map_manager.remove_map(f'{self.loaded_map.get("uuid")}.Map.Gbx', True)
            self.loaded_map = None
        except:
            logger.warning("Impossible to remove map %s", self.loaded_map.get("uuid"))
            pass

    @property
    def gold_time(self) -> int:
        if self.event_map:
            return self.event_map.time_bronze
        return 0

    @property
    def at_time(self) -> int:
        if self.event_map:
            return self.event_map.time_silver
        return 0
