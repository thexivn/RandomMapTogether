from dataclasses import dataclass
from pyplanet.apps.core.maniaplanet.models import Player
from ..models.enums.medals import Medals

@dataclass
class PlayerConfiguration:
    player: Player
    goal_medal: Medals = None
    skip_medal: Medals = None
    enabled: bool = None
