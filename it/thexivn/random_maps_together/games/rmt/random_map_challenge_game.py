import asyncio



from . import RMTGame
from ...models.enums.game_modes import GameModes
from ...configuration.rmc_configuration import RMCConfig
from ...views.rmt.random_map_challenge.settings import RandomMapChallengeSettingsView
from ...views.rmt.random_map_challenge.ingame import RandomMapChallengeIngameView

class RandomMapChallengeGame(RMTGame):
    def __init__(self, app, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.game_mode = GameModes.RANDOM_MAP_CHALLENGE
        self.config = RMCConfig(app)
        self.views.settings_view = RandomMapChallengeSettingsView(app, self.config)
        self.views.ingame_view = RandomMapChallengeIngameView(self)
        asyncio.gather(
            self.views.settings_view.display(),
            self.hide_timer()
        )
