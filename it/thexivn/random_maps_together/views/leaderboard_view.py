import logging
from typing import List, Dict
from pyplanet.apps.config import AppConfig
from pyplanet.views.generics.list import ManualListView

from ..models.database.rmt.random_maps_together_score import RandomMapsTogetherScore
# pylint: disable=duplicate-code
logger = logging.getLogger(__name__)

class LeaderboardView(ManualListView): # pylint: disable=duplicate-code
    app: AppConfig = None

    title = 'Leaderboard' # pylint: disable=duplicate-code
    template_name = "random_maps_together/list.xml"
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'

    data: List[Dict] = []

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui

    async def get_fields(self):
        return [
            {
                'name': 'Game mode',
                'index': 'game_mode',
                'sorting': True,
                'searching': True,
                'width': 35,
                'type': 'label',
                'action': self.display_score_board,
            },
            {
                'name': 'Goal',
                'index': 'goal_medal',
                'sorting': True,
                'searching': False,
                'width': 15,
                'action': self.display_score_board,
            },
            {
                'name': 'Skip',
                'index': 'skip_medal',
                'sorting': True,
                'searching': False,
                'width': 15,
                'action': self.display_score_board,
            },
            {
                'name': 'Total goal',
                'index': 'total_goal_medals',
                'sorting': True,
                'searching': False,
                'width': 20,
                'action': self.display_score_board,
            },
            {
                'name': 'Total skip',
                'index': 'total_skip_medals',
                'sorting': True,
                'searching': False,
                'width': 20,
                'action': self.display_score_board,
            },
            {
                'name': 'Medal sum',
                'index': 'medal_sum',
                'sorting': True,
                'searching': False,
                'width': 25,
                'action': self.display_score_board,
            },
            {
                'name': 'Modified player settings',
                'index': 'modified_player_settings',
                'sorting': True,
                'searching': False,
                'width': 30,
                'action': self.display_score_board,
            },
            {
                'name': 'Game time',
                'index': 'game_time_seconds',
                'sorting': True,
                'searching': False,
                'width': 20,
                'action': self.display_score_board,
            },
            {
                'name': 'Total time',
                'index': 'total_time',
                'sorting': True,
                'searching': False,
                'width': 20,
                'action': self.display_score_board,
            },
        ]


    async def get_data(self):
        return list(await RandomMapsTogetherScore.execute(
            RandomMapsTogetherScore.select()
            .where(RandomMapsTogetherScore.game_mode == self.app.game.game_mode.value)
            .order_by(
                RandomMapsTogetherScore.modified_player_settings,
                RandomMapsTogetherScore.total_goal_medals.desc(),
                RandomMapsTogetherScore.total_skip_medals.desc()
            ).dicts()
        ))

    async def display_score_board(self, player, values, row, **_kwargs): # pylint: disable=unused-argument
        self.app.game.views.scoreboard_view.game_score = await RandomMapsTogetherScore.get(
            RandomMapsTogetherScore.id == row["id"] # pylint: disable=no-member
        )
        await self.app.game.views.scoreboard_view.display([player.login])
