from dataclasses import dataclass

from .. import GameViews
from ....views.rmt.settings import RandomMapsTogetherSettingsView
from ....views.rmt.ingame import RandomMapsTogetherIngameView
from ....views.rmt.scoreboard import RandomMapsTogetherScoreBoardView

@dataclass
class RandomMapsTogetherViews(GameViews):
    settings_view: RandomMapsTogetherSettingsView = None
    ingame_view: RandomMapsTogetherIngameView = None
    scoreboard_view: RandomMapsTogetherScoreBoardView = None
