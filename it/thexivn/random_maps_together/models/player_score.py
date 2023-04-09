from dataclasses import dataclass
from pyplanet.apps.core.maniaplanet.models import Player

@dataclass
class PlayerScore:
    player: Player
    player_goal_medals: int = 0
    player_skip_medals: int = 0
    author_medals: int = 0
    gold_medals: int = 0
    silver_medals: int = 0
    bronze_medals: int = 0
    goal_medals: int = 0
    skip_medals: int = 0
