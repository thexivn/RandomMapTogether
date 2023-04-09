from dataclasses import dataclass
from typing import Dict
from pyplanet.apps.config import AppConfig

from ..models.enums.medals import Medals
from ..map_generator import MapGenerator
from ..models.player_configuration import PlayerConfiguration

@dataclass
class Configuration:
    app: AppConfig
    goal_medal = Medals.AUTHOR
    skip_medal = Medals.GOLD
    enabled = True
    min_level_to_start = 1
    map_generator = None
    player_configs: Dict[str, PlayerConfiguration] = None

    def __post_init__(self):
        self.map_generator = MapGenerator(self.app)
        self.update_player_configs()

    def set_min_level_to_start(self, old_value: str, value: str):
        level = int(value)
        if level < 0:
            level = 0
        elif level > 3:
            level = 3

        self.min_level_to_start = level

    async def update_time_left(self, rmt_game, free_skip=False, goal_medal=False, skip_medal=False):
        pass

    def update_player_configs(self):
        if not self.player_configs:
            self.player_configs = {
                player.login: PlayerConfiguration(player)
                for player in self.app.instance.player_manager.online
            }
        else:
            for player in self.app.instance.player_manager.online:
                if not player.login in self.player_configs:
                    self.player_configs[player.login] = PlayerConfiguration(player)
