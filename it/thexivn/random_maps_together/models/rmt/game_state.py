from dataclasses import dataclass, field
from typing import Optional, Union

from pyplanet.apps.core.maniaplanet.models import Player
from ..enums.medals import Medals
from ..round_timer import RoundTimer

@dataclass
class GameState:
    round_timer: RoundTimer = field(default_factory=RoundTimer)
    time_left: Union[int, float] = 0
    penalty_skips: int = 0
    current_map_completed: bool = True
    skip_medal_player: Optional[Player] = None
    skip_medal: Optional[Medals] = None
    is_paused: bool = False
