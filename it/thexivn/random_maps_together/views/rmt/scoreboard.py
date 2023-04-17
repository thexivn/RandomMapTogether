import asyncio
import logging
import time as py_time

from pyplanet.views import TemplateView
from pyplanet.apps.core.maniaplanet.models import Player

from ...models.enums.medal_urls import MedalURLs
from ...models.database.rmt.random_maps_together_player_score import RandomMapsTogetherPlayerScore

logger = logging.getLogger(__name__)

class RandomMapsTogetherScoreBoardView(TemplateView):
    template_name = "random_maps_together/rmt/scoreboard.xml"

    def __init__(self, game):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.game = game
        self.manager = game.app.context.ui
        self.game_score = None
        self.id = "it_thexivn_RandomMapsTogether_scoreboard"
        self._player_loops = {}
        self.subscribe("ui_hide_scoreboard", self.hide_scoreboard_for_player)

    async def get_context_data(self):
        data = await super().get_context_data()
        data["game"] = self.game
        data["total_goal_medals"] = self.game_score.total_goal_medals
        data["total_skip_medals"] = self.game_score.total_skip_medals
        data["goal_medal_url"] = MedalURLs[self.game_score.goal_medal].value
        data["skip_medal_url"] = MedalURLs[self.game_score.skip_medal].value
        data["medal_urls"] = MedalURLs

        data["players"] = await RandomMapsTogetherPlayerScore.get_top_20_players(self.game_score.id)
        data["time_left"] = self.game.time_left_str()
        data["total_played_time"] = py_time.strftime('%H:%M:%S', py_time.gmtime(self.game_score.game_time_seconds + self.game_score.total_time_gained - self.game._time_left + self.game._game_state.map_played_time()))

        data["nb_players"] = len(data["players"])
        data["scroll_max"] = max(0, data["nb_players"] * 10 - 100)

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
                if self._player_loops.get(player_login):
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

    async def display_scoreboard_for_player(self, player: Player, *args, **kw):
        await self.display([player.login])

    async def hide_scoreboard_for_player(self, player: Player, *args, **kw):
        if self._is_player_shown.get(player.login) or self._is_global_shown:
            await self.hide([player.login])
