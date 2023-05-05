from dataclasses import dataclass
from typing import Optional
from pyplanet.apps.core.maniaplanet.models import Player
from ..models.enums.medals import Medals

@dataclass
class PlayerConfiguration:
    player: Player
    goal_medal: Optional[Medals] = None
    skip_medal: Optional[Medals] = None
    enabled: Optional[bool] = None
