
import io
import logging
from typing import Optional

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.contrib.map import MapManager
from pyplanet.core.storage.storage import Storage

from .models.enums.medals import Medals
from .models.api_response.api_map_info import APIMapInfo

logger = logging.getLogger(__name__)


class MapHandler:
    def __init__(self, app, map_manager: MapManager, storage: Storage):
        self._next_map: Optional[APIMapInfo] = None
        self._hub_map = '7E1heauBgOUsqlhliGDY8DoOZbm'
        self._hub_id = '63710'
        self.app = app
        self._map_manager = map_manager
        self._storage = storage
        self.active_map: Map = None
        self.pre_patch_ice = False
        self.map_is_loading = False

    async def load_with_retry(self, max_retry=3) -> bool:
        self.map_is_loading = True

        for _ in range(max_retry):
            try:
                await self.load_next_map()
                break
            except Exception as e:
                logger.error("failed to load map...", exc_info=e)
        else:
            raise RuntimeError("Failed to load map")

        self.map_is_loading = False

    async def load_next_map(self):
        logger.info('Trying to load next map ...')
        self.map_is_loading = True
        random_map = self._next_map or await self.app.game.config.map_generator.get_map()
        self._next_map = None

        map_to_remove = await self.app.instance.gbx("GetCurrentMapInfo")

        self.pre_patch_ice = random_map.is_pre_patch_ice()

        logger.info(f'TAGS: {random_map.Tags} UPDATE: {random_map.UpdatedAt}')
        logger.info(f'uploading {random_map.TrackUID}.Map.Gbx to the server...')

        await self._map_manager.upload_map(io.BytesIO(await self.app.tmx_client.get_map_content(random_map.TrackID)), f'{random_map.TrackUID}.Map.Gbx', overwrite=True)
        await self._map_manager.update_list(full_update=True, detach_fks=True)
        logger.info('UPLOAD COMPLETE')
        await self._map_manager.set_current_map(random_map.TrackUID)

        await self.remove_map(map_to_remove)

        self.app.game.config.map_generator.played_maps.add(random_map)

        self.map_is_loading = False
        logger.info('map loaded')

    async def pre_load_next_map(self):
        try:
            self._next_map = await self.app.game.config.map_generator.get_map()
        except Exception as e:
            self._next_map = None
            logger.warning('Preload failed: %s', str(e))

    async def load_hub(self):
        logger.info('loading HUB map ...')

        current_map = await self.app.instance.gbx("GetCurrentMapInfo")

        if current_map["UId"] == self._hub_map:
            logger.info("Current map is already HUB map")
        elif await self._map_exists_in_match_settings(self._hub_map):
            logger.info('HUB map was already loaded')
            await self._map_manager.set_current_map(self._hub_map)
        else:
            await self._map_manager.upload_map(io.BytesIO(await self.app.tmx_client.get_map_content(self._hub_id)), f'{self._hub_map}.Map.Gbx', overwrite=True)
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

    async def _map_exists_in_match_settings(self, uid: str) -> bool:
        return next(
            (map for map in await self.app.instance.gbx("GetMapList", -1, 0) if map["UId"] == uid),
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

    async def map_begin_event(self, map: Map, *args, **kwargs):
        self.active_map = map
