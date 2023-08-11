from dataclasses import dataclass, field
from pyplanet.views.generics.widget import WidgetView

@dataclass
class GameViews:
    settings_view: WidgetView = field(init=False)
    ingame_view: WidgetView = field(init=False)
