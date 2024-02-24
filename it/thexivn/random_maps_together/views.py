import logging
import json
import time as py_time
from typing import Optional

from pyplanet.views import TemplateView
from pyplanet.views.generics.widget import WidgetView

from apps.it.thexivn.random_maps_together.Data.GameScore import GameScore
from apps.it.thexivn.random_maps_together.Data.GameState import GameState

logger = logging.getLogger(__name__)


class RandomMapsTogetherView(WidgetView):
    widget_x = -100
    widget_y = 89
    z_index = 5
    size_x = 60
    size_y = 10
    title = ""

    template_name = "random_maps_together/widget.xml"

    def __init__(self, app):
        super().__init__()
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_widget"
        self._score: GameScore = None
        self.ui_controls_visible = True
        self._game_state: GameState = None
        self._skippable_map = False

    def set_score(self, score: GameScore):
        self._score = score

    def set_game_state(self, state: GameState):
        self._game_state = state

    def set_skippable_map(self, skip: bool):
        self._skippable_map = skip

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()
        data['ui_tools_enabled'] = self.ui_controls_visible
        if self._score:
            data["AT"] = self._score.total_at
            data["GOLD"] = self._score.total_gold
        else:
            data["AT"] = 0
            data["GOLD"] = 0

        if self._game_state:
            data["game_started"] = self._game_state.game_is_in_progress
            data["gold_skip_visible"] = self._game_state.gold_skip_available
            data["free_skip_visible"] = self._game_state.free_skip_available or self._skippable_map
            data["map_loading"] = self._game_state.map_is_loading
        else:
            data["game_started"] = False

        return data


class RMTScoreBoard(TemplateView):
    template_name = "random_maps_together/score_board.xml"

    def __init__(self, app, score: GameScore):
        super().__init__()
        logger.info("Loading VIEW")
        self.layer = "ScoresTable"
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
        data["AT"] = self._score.total_at
        data["GOLD"] = self._score.total_gold
        data["players"] = self._score.get_top(10)
        data["time_left"] = self._time_left

        return data


class MapInfoWidget(WidgetView):
    widget_x = 160
    widget_y = 88
    z_index = 30

    template_name = "random_maps_together/mapinfo.xml"

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.id = 'pyplanet__widgets_mapinfo'


class PollView(TemplateView):
    z_index = 30

    template_name = "random_maps_together/poll.xml"

    def __init__(self, app, manager):
        super().__init__()
        self.app = app
        self.manager = manager
        self.id = 'rmt_poll'


class PollUpdaterView(TemplateView):
    template_name = 'random_maps_together/updater.xml'

    def __init__(self, app, manager, *args, **kwargs):
        super().__init__()
        self.app = app
        self.manager = manager
        self.id = 'rmt__updater'

    async def get_context_data(self):
        jsondata = {
            "Votes": self.app.poll_votes,
            "Limit": int(self.app.poll_time - py_time.time()),
        }
        data = {
            "polljson": json.dumps(jsondata)
        }
        return data


class PlayerUpdaterView(TemplateView):
    template_name = "random_maps_together/player_updater.xml"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.manager = app.context.ui
        self.id = 'pyplanet__scoretable_updater'
        self.title = "Scoretable Updater"

    async def get_context_data(self):
        player_data = []
        for player in self.app.instance.player_manager.online:
            player_data.append(
                {
                    "Login": player.login,
                    "Nick": player.nickname
                })

        return {
            "playerjson": json.dumps(player_data),
            'num_players': self.app.instance.player_manager.count_players,
            'max_players': self.app.instance.player_manager.max_players,
            'num_spectators': self.app.instance.player_manager.count_spectators,
            'max_spectators': self.app.instance.player_manager.max_spectators,
        }


