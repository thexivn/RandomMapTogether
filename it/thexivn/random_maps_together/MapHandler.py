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

    async def await_next_map(self):
        while self._next_map is None:
            await asyncio.sleep(0.05)
        return self._next_map

    async def load_next_map(self):
        logger.info('Trying to load next map ...')
        random_map = self._next_map or self.app.app_settings.map_generator.get_map()
        self._next_map = None

        map_to_remove = await self.app.instance.gbx("GetCurrentMapInfo")

        self.pre_patch_ice = (TAG_BOBSLEIGH in random_map.tags or TAG_ICE in random_map.tags) and random_map.last_update < ICE_CHANGE_DATE
        logger.info(f'TAGS: {random_map.tags} UPDATE: {random_map.last_update}')
        logger.info(f'uploading {random_map.uuid}.Map.Gbx to the server...')

        await self._map_manager.upload_map(io.BytesIO(random_map.content), f'{random_map.uuid}.Map.Gbx', overwrite=True)
        await self._map_manager.update_list(full_update=True, detach_fks=True)
        logger.info('UPLOAD COMPLETE')
        await self._map_manager.set_current_map(random_map.uuid)

        await self.remove_map(map_to_remove)

        self.app.app_settings.map_generator.played_maps.append(random_map.uuid)
        logger.info('map loaded')

    async def pre_load_next_map(self):
        try:
            self._next_map = self.app.app_settings.map_generator.get_map()
        except:
            self._next_map = None
            logger.warning('Preload failed')

    async def load_hub(self):
        logger.info('loading HUB map ...')

        current_map = await self.app.instance.gbx("GetCurrentMapInfo")

        if current_map["UId"] == self._hub_map:
            logger.info("Current map is already HUB map")
        elif await self._map_exists_in_match_settings(self._hub_map):
            logger.info('HUB map was already loaded')
            await self._map_manager.set_current_map(self._hub_map)
        else:
            content = self.app.app_settings.map_generator.get_map_content(self._hub_id)
            await self._map_manager.upload_map(io.BytesIO(content), f'{self._hub_map}.Map.Gbx', overwrite=True)
            await self._map_manager.update_list(full_update=True, detach_fks=True)
            await self._map_manager.set_current_map(self._hub_map)

        await self.remove_unused_maps()
        logger.info("Welcome to the HUB")

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

    async def _map_exists_in_match_settings(self, uuid: str) -> bool:
        return next(
            (map for map in await self.app.instance.gbx("GetMapList", -1, 0) if map["UId"] == uuid),
            None
        )

    async def remove_map(self, map):
        # Remove from match settings
        if await self._map_exists_in_match_settings(map["UId"]):
            try:
                await self.app.instance.gbx("RemoveMap", map["FileName"])
                logger.info(f"Removed map from match settings: : {map['FileName']}")
            except Exception:
                logger.info(f"Failed to remove map from match settings: : {map['FileName']}")

        # Remove from drive
        try:
            if map["UId"] != self._hub_map:
                await self.app.instance.storage.remove_map(map["FileName"])
                logger.info(f"Successfully removed map from drive: {map['FileName']}")
        except Exception:
            logger.error(f"Failed to removed map from drive: {map['FileName']}")
            pass

    async def remove_unused_maps(self):
        for map in await self.app.instance.gbx("GetMapList", 100, 0):
            if map["UId"] != self._hub_map:
                await self.remove_map(map)
