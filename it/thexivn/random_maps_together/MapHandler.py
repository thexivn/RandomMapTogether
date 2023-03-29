import asyncio
import io
import logging
from typing import Optional

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager
from pyplanet.contrib.map.exceptions import MapNotFound, MapException
from pyplanet.core.storage.storage import Storage
from pyplanet.core.instance import Instance

from .Data.Constants import TAG_BOBSLEIGH, TAG_ICE, ICE_CHANGE_DATE
from .Data.Medals import Medals
from .Data.APIMapInfo import APIMapInfo
from .map_generator import MapGenerator

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, app, map_manager: MapManager, storage: Storage):
        self._hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self._hub_id = '63710'
        self._map_manager = map_manager
        self._storage = storage
        self.app = app
        self.active_map: Map = None
        self.pre_patch_ice = False
        self._next_map: Optional[APIMapInfo] = None
        self.map_generator = MapGenerator()

    async def await_next_map(self):
        while self._next_map is None:
            await asyncio.sleep(0.05)
        return self._next_map

    async def load_next_map(self):
        logger.info('Trying to load next map ...')
        random_map = self._next_map or self.map_generator.get_map()

        self._next_map = None
        map_to_remove = self._map_manager.current_map
        self.pre_patch_ice = (TAG_BOBSLEIGH in random_map.tags or TAG_ICE in random_map.tags) and random_map.last_update < ICE_CHANGE_DATE
        logger.info(f'TAGS: {random_map.tags} UPDATE: {random_map.last_update}')
        logger.info(f'uploading {random_map.uuid}.Map.Gbx to the server...')

        await self._map_manager.upload_map(io.BytesIO(random_map.content), f'{random_map.uuid}.Map.Gbx', overwrite=True)
        await self._map_manager.update_list(full_update=True, detach_fks=True)
        logger.info('UPLOAD COMPLETE')
        await self._map_manager.set_current_map(random_map.uuid)
        await self._map_manager.remove_map(map_to_remove, delete_file=True)

        logger.info('map loaded')
        self.map_generator.played_maps.append(self.active_map.uid)

    async def pre_load_next_map(self):
        try:
            self._next_map = self.map_generator.get_map()
        except:
            self._next_map = None
            logger.warning('Preload failed')

    async def load_hub(self):
        logger.info('loading HUB map ...')
        if await self._map_exists(self._hub_map):
            logger.info('HUB map was already loaded')
            await self._map_manager.set_current_map(self._hub_map)
            return

        content = self.map_generator.get_map_content(self._hub_id)
        try:
            if await self._map_manager.get_map(self._hub_map) not in self._map_manager.maps:
                content = await self._tmnx_rest_client.get_map_content(self._hub_id)
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
                await self._map_manager.remove_map(f'{uuid}.Map.Gbx', delete_file=True)
            except Exception as e:
                logger.warning('Impossible to remove map %s', await self.active_map.uid)
                logger.error('Exception: ', exc_info=e)
        else:
            logger.warning('impossible to remove map without UUID')

    def get_medal_by_time(self, race_time: int):
        if self.active_map:
            if race_time <= self.active_map.time_author:
                return Medals.AUTHOR
            elif race_time <= self.active_map.time_gold:
                return Medals.GOLD
            elif race_time <= self.active_map.time_silver:
                return Medals.SILVER
            elif race_time <= self.active_map.time_bronze:
                return Medals.BRONZE

    async def _map_exists(self, uuid: str) -> bool:
        try:
            db_map = await self._map_manager.get_map(uuid)
            return await self._storage.driver.exists(db_map.file)
        except MapNotFound as not_found:
            logger.exception('Failed to get MAP %s', uuid, exc_info=not_found)
            return False
