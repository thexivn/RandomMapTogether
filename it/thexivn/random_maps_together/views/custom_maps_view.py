import logging

from pyplanet.views.generics.list import ManualListView
from .player_prompt_view import PlayerPromptView

logger = logging.getLogger(__name__)

class CustomMapsView(ManualListView):
    app = None

    title = 'Custom Maps'
    template_name = "random_maps_together/list.xml"
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'

    data = []

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui

    async def get_fields(self):
        return [
            {
                'name': 'Name',
                'index': 'name',
                'sorting': True,
                'searching': True,
                'width': 50,
                'type': 'label',
            },
            {
                'name': 'Author',
                'index': 'author',
                'sorting': True,
                'searching': False,
                'width': 50,
            },
            {
                'name': 'Tags',
                'index': 'tags',
                'sorting': True,
                'searching': False,
                'width': 50,
                'safe': True
            },
            {
                'name': 'Pre patch ice',
                'index': 'pre_patch_ice',
                'sorting': True,
                'searching': False,
                'width': 30,
                'safe': True
            },
            {
                'name': 'ID',
                'index': 'id',
                'sorting': True,
                'searching': True,
                'width': 30,
                'type': 'label',
            },
        ]

    async def get_actions(self):
        return [
            {
                    'name': 'Remove',
                    'action': self.remove_map,
                    'style': 'Icons64x64_1',
                    'substyle': 'Close',
            },
        ]

    async def get_buttons(self):
        return [
            {
                "title": "Add map",
                "width": 30,
                "action": self.add_map
            },
            {
                "title": "Add map pack",
                "width": 30,
                "action": self.add_map_pack
            },
        ]

    async def get_data(self):
        data = [
            {
                "name": map.Name,
                "author": map.Username,
                "tags": ", ".join([str(tag) for tag in map.Tags]),
                "pre_patch_ice": map.is_pre_patch_ice(),
                "id": map.TrackID,
                "uid": map.TrackUID,
            }
            for map in self.app.app_settings.map_generator.maps
        ]
        logger.info(data)
        return data

    async def remove_map(self, player, values, map, **kwargs):
        await self.app.app_settings.map_generator.remove_map(map["id"])
        await self.display(player)

    async def add_map(self, player, values, **kwargs):
        map_id = await PlayerPromptView.prompt_for_input(player, "Map ID", validator=self.app.app_settings.map_generator.map_id_validator, default="")
        await self.app.app_settings.map_generator.add_map(map_id)
        await self.display(player)

    async def add_map_pack(self, player, values, **kwargs):
        map_pack_id = await PlayerPromptView.prompt_for_input(player, "Map Pack ID", validator=self.app.app_settings.map_generator.map_pack_id_validator, default="")
        await self.app.app_settings.map_generator.add_map_pack(map_pack_id)
        await self.display(player)
