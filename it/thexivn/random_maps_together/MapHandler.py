import io
import logging

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager
from pyplanet.contrib.map.exceptions import MapException
from pyplanet.core.storage.storage import Storage

from it.thexivn.random_maps_together.RestClient.TMNXRestClient import TMNXRestClient

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, map_manager: MapManager, storage: Storage):
        self.tmnx_rest_client = TMNXRestClient()
        self.hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self.hub_id = '63710'
        self.map_manager = map_manager
        self.loaded_map = None
        self.event_map: Map = None
        self._sotorage = storage

    async def load_next_map(self):
        logger.info("Trying to load next map ...")
        self.loaded_map = self.tmnx_rest_client.get_random_map()
        map_to_remove = self.map_manager.current_map
        logger.info(f'{self.loaded_map.get("uuid")}.Map.Gbx')
        await self.upload_map_new(io.BytesIO(self.loaded_map.get("content")),
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
            await self.upload_map_new(io.BytesIO(content), f'{self.hub_id}.Map.Gbx', overwrite=True)
            await self.map_manager.update_list(True, True)
            await self.map_manager.set_current_map(self.hub_map)
        except:
            pass

        logger.info("hub map loaded")

    async def remove_loaded_map(self):
        uuid = self.loaded_map.get("uuid")
        if uuid:
            try:
                await self.map_manager.remove_map(f'{uuid}.Map.Gbx', True)
                self.loaded_map = None
            except:
                logger.warning("Impossible to remove map %s", self.loaded_map.get("uuid"))
                pass
        else:
            logger.warning("impossible to remove map without UUID")

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


    async def upload_map_new(self, fh, filename, insert=True, overwrite=False):
        """
        Upload and add/insert the map to the current online playlist.

        :param fh: File handler, bytesio object or any readable context.
        :param filename: The filename when saving on the server. Must include the map.gbx! Relative to 'Maps' folder.
        :param insert: Insert after the current map, this will make it play directly after the current map. True by default.
        :param overwrite: Overwrite current file if exists? Default False.
        :type filename: str
        :type insert: bool
        :type overwrite: bool
        :raise: pyplanet.contrib.map.exceptions.MapIncompatible
        :raise: pyplanet.contrib.map.exceptions.MapException
        :raise: pyplanet.core.storage.exceptions.StorageException
        """
        exists = await self._sotorage.driver.exists(filename)
        if exists and not overwrite:
            raise MapException('Map with filename already located on server!')
        if not exists:
            await self._sotorage.driver.touch('{}/{}'.format(self._instance.storage.MAP_FOLDER, filename))

        async with self._sotorage.open_map(filename, 'wb+') as fw:
            await fw.write(fh.read(-1))

        return await self.map_manager.add_map(filename, insert=insert)