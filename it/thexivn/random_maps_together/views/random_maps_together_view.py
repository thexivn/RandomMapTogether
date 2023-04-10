import logging
from ..models.enums.game_modes import GameModes
from ..models.enums.medal_urls import MedalURLs
from ..models.game_score import GameScore
from ..models.game_state import GameState
from pyplanet.views.generics.widget import TimesWidgetView

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

class RandomMapsTogetherView(TimesWidgetView):
    widget_x = -100
    widget_y = 86
    z_index = 5
    size_x = 66
    size_y = 9
    title = "  Random Maps Together++  "

    template_name = "random_maps_together/widget.xml"

    async def render(self, *args, **kwargs):
        # print('render')
        ret = await super().render(*args, **kwargs)
        # print(f'render output: {ret}')
        return ret

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

        data["settings"] = self.app.app_settings

        if self._score:
            data["total_goal_medals"] = self._score.total_goal_medals
            data["total_skip_medals"] = self._score.total_skip_medals
        else:
            data["total_goal_medals"] = 0
            data["total_skip_medals"] = 0

        data["ui_tools_enabled"] = self.ui_controls_visible
        if self._game_state:
            data["is_paused"] = self._game_state.is_paused
            data["goal_medal_url"] = MedalURLs[self.app.app_settings.goal_medal.name].value
            data["skip_medal_url"] = MedalURLs[self.app.app_settings.skip_medal.name].value
            data["game_started"] = self._game_state.game_is_in_progress
            data["skip_medal"] = self._game_state.skip_medal
            data["allow_pausing"] = self.app.app_settings.allow_pausing
            if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_CHALLENGE:
                data["free_skip_visible"] = self._game_state.free_skip_available or self.app.app_settings.infinite_free_skips
            if self.app.app_settings.game_mode == GameModes.RANDOM_MAP_SURVIVAL:
                data["free_skip_visible"] = True
            data["skip_pre_patch_ice_visible"] = self.app.map_handler.pre_patch_ice
            data["map_loading"] = self._game_state.map_is_loading
        else:
            data["game_started"] = False

        data['cb_pos'] = cb_pos
        data['cbl_pos'] = cbl_pos

        data['btn_pos_size'] = in_game_btn_pos(self.size_x, 2)# 3 if self.app.app_settings.allow_pausing else 2)

        return data
