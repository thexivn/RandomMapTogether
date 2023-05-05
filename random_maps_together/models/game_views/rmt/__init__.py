from dataclasses import dataclass, field
from typing import Optional

from .. import GameViews
from ....views.rmt.settings import RandomMapsTogetherSettingsView
from ....views.rmt.ingame import RandomMapsTogetherIngameView
from ....views.rmt.scoreboard import RandomMapsTogetherScoreBoardView

@dataclass
class RandomMapsTogetherViews(GameViews):
    settings_view: RandomMapsTogetherSettingsView = field(init=False)
    ingame_view: RandomMapsTogetherIngameView = field(init=False)
    scoreboard_view: RandomMapsTogetherScoreBoardView = field(init=False)
