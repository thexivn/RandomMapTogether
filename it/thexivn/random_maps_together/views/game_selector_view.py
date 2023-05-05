import logging
from dataclasses import fields
from pyplanet.views.generics.widget import WidgetView
from pyplanet.apps.core.maniaplanet.models import Player
from ..models.enums.game_modes import GameModes
from ..games.rmt.random_map_challenge_game import RandomMapChallengeGame
from ..games.rmt.random_map_survival_game import RandomMapSurvivalGame
from ..games import check_player_allowed_to_change_game_settings
from ..views.player_prompt_view import PlayerPromptView

logger = logging.getLogger(__name__)

class GameSelectorView(WidgetView):
    widget_x = -100
    widget_y = 86
    z_index = 5
    size_x = 35
    size_y = 6
    title = "Game HUB"
    action = None
    distraction_hide = True

    template_name = "random_maps_together/game_selector.xml"

    def __init__(self, app):
        super().__init__(self)
        logger.info("Loading VIEW")
        self.app = app
        self.manager = app.context.ui
        self.id = "it_thexivn_RandomMapsTogether_game_selector"
        self.subscribe("ui_set_game_mode", self.set_game_mode)

    async def get_context_data(self):
        context = await super().get_context_data()
        context["game_mode"] = self.app.game.game_mode.value
        return context


    @check_player_allowed_to_change_game_settings
    async def set_game_mode(self, player: Player, *_args, **_kwargs):
        buttons = [
            {"name": game_mode.value, "value": game_mode}
            for game_mode in GameModes
        ]
        new_game_mode = await PlayerPromptView.prompt_for_input(player, "Choose Game Mode", buttons, entry=False)
        if new_game_mode == self.app.game.game_mode:
            return

        for field in fields(self.app.game.views.__class__):
            view = getattr(self.app.game.views, field.name)
            if view:
                await view.destroy()

        if new_game_mode == GameModes.RANDOM_MAP_CHALLENGE:
            self.app.game = RandomMapChallengeGame(self.app)
        if new_game_mode == GameModes.RANDOM_MAP_SURVIVAL:
            self.app.game = RandomMapSurvivalGame(self.app)

        await self.display()
