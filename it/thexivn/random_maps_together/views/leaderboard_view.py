import logging
from pyplanet.views.generics.list import ManualListView

from ..models.database.rmt.random_maps_together_score import RandomMapsTogetherScore

logger = logging.getLogger(__name__)

class LeaderboardView(ManualListView):
    app = None

    title = 'Leaderboard'
    template_name = "random_maps_together/list.xml"
    icon_style = 'Icons128x128_1'
    icon_substyle = 'Browse'

    data = []

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui

    async def get_fields(self):
        return [
            {
                'name': 'Game ID',
                'index': 'id',
                'sorting': True,
                'searching': True,
                'width': 10,
                'type': 'label',
                'action': self.display_score_board,
            },
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
                'name': 'Gained time',
                'index': 'total_time_gained',
                'sorting': True,
                'searching': False,
                'width': 20,
                'action': self.display_score_board,
            },
        ]


    async def get_data(self):
        return await RandomMapsTogetherScore.execute(
            RandomMapsTogetherScore.select()
            .where(RandomMapsTogetherScore.game_mode == self.app.game.game_mode.value)
            .order_by(
                RandomMapsTogetherScore.modified_player_settings,
                RandomMapsTogetherScore.total_goal_medals.desc(),
                RandomMapsTogetherScore.total_skip_medals.desc()
            )
        )

    async def display_score_board(self, player, values, row, **kwargs):
        self.app.game.views.scoreboard_view.game_score = row
        await self.app.game.views.scoreboard_view.display()
