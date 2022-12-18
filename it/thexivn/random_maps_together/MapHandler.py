import asyncio
import io
import logging
from typing import Optional

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager
from pyplanet.contrib.map.exceptions import MapNotFound
from pyplanet.core.storage.storage import Storage

from it.thexivn.random_maps_together import AT, GOLD, SILVER, BRONZE, TAG_BOBSLEIGH, TAG_ICE, ICE_CHANGE_DATE
from it.thexivn.random_maps_together.Data import Configurations
from it.thexivn.random_maps_together.Data.APIMapInfo import APIMapInfo
from it.thexivn.random_maps_together.RestClient.TMNXRestClient import TMNXRestClient

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, map_manager: MapManager, storage: Storage, configs: Configurations):
        self._tmnx_rest_client = TMNXRestClient()
        self._hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self._hub_id = '63710'
        self._map_manager = map_manager
        self._storage = storage
        self._configs: Configurations = configs
        self.active_map: Map = None
        self.current_map_is_skipable = False
        self._nex_map: Optional[APIMapInfo] = None

    async def load_next_map(self):
        logger.info('Trying to load next map ...')
        random_map = self._nex_map if self._nex_map else self._tmnx_rest_client.get_random_map()
        self._nex_map = None
        map_to_remove = self._map_manager.current_map
        self.current_map_is_skipable = (TAG_BOBSLEIGH in random_map.tags or TAG_ICE in random_map.tags) and random_map.last_update < ICE_CHANGE_DATE
        logger.info(f'TAGS: {random_map.tags} UPDATE: {random_map.last_update}')
        logger.info(f'uploading {random_map.uuid}.Map.Gbx to the server...')
        await self._map_manager.upload_map(io.BytesIO(random_map.content),
                                           f'{random_map.uuid}.Map.Gbx', overwrite=True)
        await self._map_manager.update_list(True, True)
        logger.info('UPLOAD COMPLETE')
        await self._map_manager.set_current_map(random_map.uuid)
        await self._map_manager.remove_map(map_to_remove, True)
        logger.info('map loaded')

    def pre_load_next_map(self):
        try:
            self._nex_map = self._tmnx_rest_client.get_random_map()
        except:
            self._nex_map = None
            logger.warning('Preload failed')

    async def load_hub(self):
        logger.info('loading HUB map ...')
        if await self._map_exists(self._hub_map):
            logger.info('HUB map was already loaded')
            await self._map_manager.set_current_map(self._hub_map)
            return

        content = self._tmnx_rest_client.map_map_content(self._hub_id)
        try:
            await self._map_manager.upload_map(io.BytesIO(content), f'{self._hub_id}.Map.Gbx', overwrite=True)
            await self._map_manager.update_list(True, True)
            await self._map_manager.set_current_map(self._hub_map)
            logger.info("Welcome to the HUB")
        except Exception as e:
            logger.error('Exception while loading the HUB', exc_info=e)

    async def remove_loaded_map(self):
        if self.active_map:
            uuid = self.active_map.uid
            if uuid == self._hub_map:
                logger.info('Skip deletion of HUB MAP')
                return
            try:
                await self._map_manager.remove_map(f'{uuid}.Map.Gbx', True)
            except Exception as e:
                logger.warning('Impossible to remove map %s', self.loaded_map.get('uuid'))
                logger.error('Exception: ', exc_info=e)
        else:
            logger.warning('impossible to remove map without UUID')

    @property
    def gold_time(self) -> int:
        if self.active_map:
            difficulty = self._configs.GOLD_time
            if difficulty == GOLD:
                return self.active_map.time_gold
            elif difficulty == SILVER:
                return self.active_map.time_silver
            elif difficulty == BRONZE:
                return self.active_map.time_bronze
        return 0

    @property
    def at_time(self) -> int:
        if self.active_map:
            difficulty = self._configs.AT_time
            if difficulty == AT:
                return self.active_map.time_author
            elif difficulty == GOLD:
                return self.active_map.time_gold
            elif difficulty == SILVER:
                return self.active_map.time_silver

        return 0

    async def _map_exists(self, uuid: str) -> bool:
        try:
            db_map = await self._map_manager.get_map(uuid)
            return await self._storage.driver.exists(db_map.file)
        except MapNotFound as not_found:
            logger.exception('Failed to get MAP %s', uuid, exc_info=not_found)
            return False
