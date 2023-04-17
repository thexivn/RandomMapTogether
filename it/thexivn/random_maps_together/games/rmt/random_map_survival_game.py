import asyncio

from . import RMTGame
from ...models.enums.game_modes import GameModes
from ...configuration.rmt.rms_configuration import RMSConfig
from ...views.rmt.random_map_survival.settings import RandomMapSurvivalSettingsView
from ...views.rmt.random_map_survival.ingame import RandomMapSurvivalIngameView

class RandomMapSurvivalGame(RMTGame):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.game_mode = GameModes.RANDOM_MAP_SURVIVAL
        self.config = RMSConfig(app)
        self.views.settings_view = RandomMapSurvivalSettingsView(app, self.config)
        self.views.ingame_view = RandomMapSurvivalIngameView(self)
        asyncio.gather(
            self.views.settings_view.display(),
            self.hide_timer()
        )