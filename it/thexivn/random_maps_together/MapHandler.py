import io
import logging

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager

from it.thexivn.random_maps_together.RestClient.TMNXRestClient import TMNXRestClient
from pyplanet.apps.core.maniaplanet import callbacks as mania_callbacks

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, map_manager: MapManager):
        self.tmnx_rest_client = TMNXRestClient()
        self.hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self.hub_id = '63710'
        self.map_manager = map_manager
        self.loaded_map = None
        self.AT = 0

    async def on_init(self):
        logger.info("MapHandler loaded")
        await self.load_hub()
        mania_callbacks.map.map_begin.register(self.map_begin)

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

    def map_begin(self, map: Map, *args, **kwargs):
        logging.info("Map Loaded: %s -- AT %d", map.name, map.time_author)
        self.AT = map.time_bronze

