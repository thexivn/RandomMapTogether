import logging
from pyplanet.views.generics.widget import WidgetView

from ...models.enums.game_modes import GameModes
from ...models.enums.medal_urls import MedalURLs

logger = logging.getLogger(__name__)

cb_y_off = 3

def cb_pos(n):
    return f".2 {-23.8 - (5.4 * n) - cb_y_off:.2f}"

def cbl_pos(n):
    return f"6.5 {-23.3 - (5.4 * n) - cb_y_off:.2f}"

def in_game_btn_pos(size_x, n_btns):
    def btn_pos(btn_ix):
        # this does basically nothing b/c of the style used for the buttons
        btn_margin = 3
        total_margins = (2 * n_btns + 1) * btn_margin
        btn_width = (size_x - total_margins) / n_btns
        btn_x_off = (btn_margin * 2 + btn_width) * btn_ix + btn_margin
        ret = f"pos=\"{btn_x_off:.2f} -3\" size=\"{btn_width:.2f} 4\""
        # logging.info(f"btn_pos returning: {ret}")
        return ret
    return btn_pos

class RandomMapsTogetherIngameView(WidgetView):
    widget_x = -100
    widget_y = 86
    z_index = 5
    size_x = 66
    size_y = 9

    template_name = "random_maps_together/rmt/ingame.xml"

    def __init__(self, game):
        super().__init__()
        logger.info("Loading VIEW")
        self.id = "it_thexivn_RandomMapsTogether_ingame"
        self.game = game
        self.manager = game.app.context.ui

        self.subscribe("ui_stop", self.game.app.stop_game)
        self.subscribe("ui_skip_medal", self.game.command_skip_medal)
        self.subscribe("ui_free_skip", self.game.command_free_skip)
        self.subscribe("ui_display_player_settings", self.game.config.display_player_settings)
        self.subscribe("ui_toggle_pause", self.game.command_toggle_pause)
        self.subscribe("ui_display_scoreboard", self.game.views.scoreboard_view.display_scoreboard_for_player)

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["game"] = self.game

        data["total_goal_medals"] = self.game._score.total_goal_medals
        data["total_skip_medals"] = self.game._score.total_skip_medals

        data["is_paused"] = self.game._game_state.is_paused
        data["goal_medal_url"] = MedalURLs[self.game.config.goal_medal.name].value
        data["skip_medal_url"] = MedalURLs[self.game.config.skip_medal.name].value
        data["game_started"] = self.game.game_is_in_progress
        data["skip_medal"] = self.game._game_state.skip_medal
        data["allow_pausing"] = self.game.config.allow_pausing
        data["skip_pre_patch_ice_visible"] = self.game.app.map_handler.pre_patch_ice
        data["map_loading"] = self.game.app.map_handler.map_is_loading

        data['cb_pos'] = cb_pos
        data['cbl_pos'] = cbl_pos

        data['btn_pos_size'] = in_game_btn_pos(self.size_x, 2)

        return data
