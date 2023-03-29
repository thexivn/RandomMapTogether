import logging
from typing import Optional
import time as py_time

from pyplanet.views import TemplateView
from pyplanet.views.generics.widget import TimesWidgetView

from .Data.GameScore import GameScore
from .Data.GameState import GameState
from .Data.MedalURLs import MedalURLs
from .Data.GameModes import GameModes

logger = logging.getLogger(__name__)


class RandomMapsTogetherView(TimesWidgetView):
    widget_x = -100
    widget_y = 89
    z_index = 5
    size_x = 66
    size_y = 9
    title = "Random Maps Together"

    template_name = "random_maps_together/widget.xml"

    def __init__(self, app):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_widget"
        self._score: GameScore = None
        self.ui_controls_visible = True
        self._game_state: GameState = None

    def set_score(self, score: GameScore):
        self._score = score

    def set_game_state(self, state: GameState):
        self._game_state = state

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["settings"] = self.app.app_settings

        if self._score:
            data["total_goal_medals"] = self._score.total_goal_medals
            data["total_skip_medals"] = self._score.total_skip_medals
        else:
            data["total_goal_medals"] = 0
            data["total_skip_medals"] = 0

        data["ui_tools_enabled"] = self.ui_controls_visible
        if self._game_state:
            data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.name].value
            data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.name].value
            data["game_started"] = self._game_state.game_is_in_progress
            data["skip_medal_visible"] = self._game_state.skip_medal_available
            if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_CHALLENGE:
                data["free_skip_visible"] = self._game_state.free_skip_available or self.app.app_settings.infinite_free_skips
            if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_SURVIVAL:
                data["free_skip_visible"] = True
            data["skip_pre_patch_ice_visible"] = self.app.map_handler.pre_patch_ice
            data["map_loading"] = self._game_state.map_is_loading
        else:
            data["game_started"] = False

        return data


class RMTScoreBoard(TemplateView):
    template_name = "random_maps_together/score_board.xml"

    def __init__(self, app, score: GameScore, game_state):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_score_board"
        self._score: GameScore = score
        self._time_left: Optional[str] = None
        self._game_state = game_state

    def set_time_left(self, time_left_seconds: int):
        self._time_left = py_time.strftime('%H:%M:%S', py_time.gmtime(time_left_seconds))

    async def get_context_data(self):
        data = await super().get_context_data()
        data["settings"] = self.app.app_settings
        data["total_goal_medals"] = self._score.total_goal_medals
        data["total_skip_medals"] = self._score.total_skip_medals
        data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.name].value
        data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.name].value
        data["medal_urls"] = MedalURLs

        data["players"] = self._score.get_top_10()
        data["time_left"] = self._time_left
        data["total_played_time"] = py_time.strftime('%H:%M:%S', py_time.gmtime(py_time.time() - self._game_state.start_time))

        return data
