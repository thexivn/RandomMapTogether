import asyncio
import logging
import time as py_time
from pyplanet.views import TemplateView

from ..models.enums.medal_urls import MedalURLs
from ..models.game_score import GameScore
from ..models.game_state import GameState

logger = logging.getLogger(__name__)

class RMTScoreBoardView(TemplateView):
    template_name = "random_maps_together/score_board.xml"

    def __init__(self, app, score: GameScore, game_state: GameState, game):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_score_board"
        self._score: GameScore = score
        self._game_state = game_state
        self._game = game
        self._player_loops = {}

    async def get_context_data(self):
        data = await super().get_context_data()
        data["settings"] = self.app.app_settings
        data["total_goal_medals"] = self._score.total_goal_medals
        data["total_skip_medals"] = self._score.total_skip_medals
        data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.name].value
        data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.name].value
        data["medal_urls"] = MedalURLs

        data["players"] = self._score.get_top_10(20)
        data["time_left"] = self._game.time_left_str()
        data["total_played_time"] = py_time.strftime('%H:%M:%S', py_time.gmtime(self.app.app_settings.game_time_seconds + self._game_state.total_time_gained - self._game._time_left + self._game_state.map_played_time()))

        data["nb_players"] = len(data['players'])
        data["scroll_max"] = max(0, len(data['players']) * 10 - 100)

        return data

    async def display(self, player_logins=None):
        if player_logins:
            for player_login in player_logins:
                self._player_loops[player_login] = asyncio.create_task(self.display_and_update_until_hide(player_login))
        else:
            await super().display()

    async def hide(self, player_logins=None):
        if player_logins:
            for player_login in player_logins:
                self._player_loops[player_login].cancel()
                del self._player_loops[player_login]
                await super().hide([player_login])
        else:
            await super().hide()

    async def display_and_update_until_hide(self, player_login=None):
        if player_login:
            await super().display([player_login])
            while player_login in self._is_player_shown:
                await asyncio.sleep(1)
                await super().display([player_login])
