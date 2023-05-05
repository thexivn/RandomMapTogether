from dataclasses import dataclass
from typing import Optional, Union
import time as py_time

from pyplanet.apps.core.maniaplanet.models import Player
from .enums.medals import Medals

@dataclass
class GameState:
    start_time: Union[int, float] = 0
    map_start_time: Union[int, float] = 0
    current_map_completed: bool = True
    free_skip_available: bool = True
    skip_medal_player: Optional[Player] = None
    skip_medal: Optional[Medals] = None
    is_paused = False

    def map_played_time(self):
        if self.current_map_completed:
            return 0
        return int(py_time.time() - self.map_start_time - 1)
