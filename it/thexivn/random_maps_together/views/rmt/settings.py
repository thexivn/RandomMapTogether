import logging

from ..settings import SettingsView

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

class RandomMapsTogetherSettingsView(SettingsView):

    def __init__(self, app, config):
        super().__init__(app, config)
        self.subscribe("ui_set_game_time_seconds", self.config.set_game_time_seconds)

        self.subscribe("ui_set_goal_medal_author", self.config.set_goal_medal)
        self.subscribe("ui_set_goal_medal_gold", self.config.set_goal_medal)
        self.subscribe("ui_set_goal_medal_silver", self.config.set_goal_medal)

        self.subscribe("ui_set_skip_medal_gold", self.config.set_skip_medal)
        self.subscribe("ui_set_skip_medal_silver", self.config.set_skip_medal)
        self.subscribe("ui_set_skip_medal_bronze", self.config.set_skip_medal)

        self.subscribe("ui_toggle_enabled_players", self.config.toggle_enabled_players)

    async def get_context_data(self):
        logger.info("Context Data")
        data = await super().get_context_data()

        data["config"] = self.config

        data['cb_pos'] = cb_pos
        data['cbl_pos'] = cbl_pos

        data['btn_pos_size'] = in_game_btn_pos(self.size_x, 2)

        return data
