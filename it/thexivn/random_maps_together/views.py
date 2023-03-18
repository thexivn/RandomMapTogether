import logging
from typing import Optional

from pyplanet.views import TemplateView
from pyplanet.views.generics.widget import TimesWidgetView

from .Data.GameScore import GameScore
from .Data.GameState import GameState
from .Data.MedalURLs import MedalURLs

logger = logging.getLogger(__name__)


class RandomMapsTogetherView(TimesWidgetView):
    widget_x = -100
    widget_y = 89
    z_index = 5
    size_x = 60
    size_y = 10
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
        data["game_time_seconds"] = self.app.app_settings.game_time_seconds
        data["goal_medal"] = self.app.app_settings.goal_medal.value
        data["skip_medal"] = self.app.app_settings.skip_medal.value
        data["infinite_skips"] = int(self.app.app_settings.infinite_free_skips)
        if self._score:
            data["total_goal_medals"] = self._score.total_goal_medals
            data["total_skip_medals"] = self._score.total_skip_medals
        else:
            data["total_goal_medals"] = 0
            data["total_skip_medals"] = 0

        data["ui_tools_enabled"] = self.ui_controls_visible
        if self._game_state:
            data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.value].value
            data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.value].value
            data["game_started"] = self._game_state.game_is_in_progress
            data["skip_medal_visible"] = self._game_state.skip_medal_available
            data["free_skip_visible"] = self._game_state.free_skip_available or self.app.app_settings.infinite_free_skips
            data["skip_pre_patch_ice_visible"] = self.app.map_handler.pre_patch_ice
            data["map_loading"] = self._game_state.map_is_loading
        else:
            data["game_started"] = False

        return data


class RMTScoreBoard(TemplateView):
    template_name = "random_maps_together/score_board.xml"

    def __init__(self, app, score: GameScore):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_score_board"
        self._score: GameScore = score
        self._time_left: Optional[str] = None

    def set_time_left(self, time_left_seconds: int):
        if time_left_seconds <= 0:
            self._time_left = None
        elif time_left_seconds < 60:
            self._time_left = f'00:{time_left_seconds:02d}'
        else:
            minutes_left = int(time_left_seconds / 60)
            seconds_left = time_left_seconds - minutes_left * 60
            self._time_left = f'{minutes_left:02d}:{seconds_left:02d}'

    async def get_context_data(self):
        data = await super().get_context_data()
        data["total_goal_medals"] = self._score.total_goal_medals
        data["total_skip_medals"] = self._score.total_skip_medals
        data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.value].value
        data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.value].value

        data["players"] = self._score.get_top_10()
        data["time_left"] = self._time_left

        return data
