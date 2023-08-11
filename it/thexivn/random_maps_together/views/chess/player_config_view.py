import logging
from typing import List, Dict
from pyplanet.views.generics.list import ManualListView
from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet.models import Player

from ...configuration import check_player_allowed_to_change_game_settings
from ...models.enums.team import Team

# pylint: disable=duplicate-code
logger = logging.getLogger(__name__)

class PlayerConfigView(ManualListView): # pylint: disable=duplicate-code
    app: AppConfig = None

    title = 'Player Configs' # pylint: disable=duplicate-code
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
                'name': 'Player',
                'index': 'player_nickname',
                'sorting': True,
                'searching': True,
                'width': 70,
                'type': 'label',
            },
            {
                'name': 'Player Login',
                'index': 'player_login',
                'sorting': True,
                'searching': True,
                'width': 70,
                'type': 'label',
            },
            {
                'name': 'Team',
                'index': 'team',
                'sorting': True,
                'searching': False,
                'width': 30,
                'action': self.action_change_team
            },
            {
                'name': 'Leader',
                'index': 'leader',
                'sorting': True,
                'searching': False,
                'width': 30,
                'action': self.action_toggle_leader
            },
        ]

    async def get_data(self):
        self.app.game.config.update_player_configs()
        return [
            {
                "player_nickname": player_config.player.nickname,
                "player_login": player_config.player.login,
                "team": Team((await Player.get_by_login(player_config.player.login)).flow.team_id).name,
                "leader": player_config.leader,
            }
            for player_config in sorted(self.app.game.config.player_configs.values(), key=lambda x: x.player.nickname)
        ]

    @check_player_allowed_to_change_game_settings
    async def action_change_team(self, player, _values, row, **_kwargs):
        target_player = await Player.get_by_login(row["player_login"])
        if target_player.flow.team_id == 0:
            await self.app.instance.gbx.multicall(
                self.app.instance.gbx('ForcePlayerTeam', row["player_login"], 1)
            )
        elif target_player.flow.team_id == 1:
            await self.app.instance.gbx.multicall(
                self.app.instance.gbx('ForcePlayerTeam', row["player_login"], 0)
            )

        await self.refresh(player=player)

    @check_player_allowed_to_change_game_settings
    async def action_toggle_leader(self, player, _values, row, **_kwargs):
        self.app.game.config.player_configs[row["player_login"]].leader ^= True

        if self.app.game.config.player_configs[row["player_login"]].leader is True:
            for player_login, player_config in self.app.game.config.player_configs.items():
                player_object = await Player.get_by_login(player_login)
                if player_object.login == row["player_login"]:
                    continue

                if (player_object.flow.team_id == 0 and Team[row["team"]] == Team.WHITE) \
                     or (player_object.flow.team_id == 1 and Team[row["team"]] == Team.BLACK):
                    player_config.leader = False

        await self.refresh(player=player)

    async def team_id_to_team(self, team_id: int):
        return ["WHITE", "BLACK"][team_id]
