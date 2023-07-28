from dataclasses import dataclass
from typing import Optional
from pyplanet.apps.core.maniaplanet.models import Player

@dataclass
class PlayerConfiguration:
    player: Player
    leader: Optional[bool] = False
