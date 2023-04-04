import logging
import re
from typing import Dict, Optional
import time as py_time
from jinja2 import Template

from pyplanet.views import TemplateView
from pyplanet.views.generics.list import ManualListView
from pyplanet.views.generics.widget import TimesWidgetView
from pyplanet.views.generics.alert import AlertView

from .Data.GameScore import GameScore
from .Data.GameState import GameState
from .Data.MedalURLs import MedalURLs
from .Data.Medals import Medals
from .Data.GameModes import GameModes

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


class RMTScoreBoard(TemplateView):
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
        time_played = self.app.app_settings.game_time_seconds - self._game._time_left + getattr(self.app.app_settings, "total_time_gained", 0)
        if not self._game_state.current_map_completed and not self._game_state.map_is_loading:
            time_played += int(py_time.time() - self._game._map_start_time + .5)

        data["total_played_time"] = py_time.strftime('%H:%M:%S', py_time.gmtime(time_played))

        data["nb_players"] = len(data['players'])
        data["scroll_max"] = max(0, len(data['players']) * 10 - 100)

        return data

class PlayerConfigsView(ManualListView):
    app = None

    title = 'Player Configs'
    template_name = "random_maps_together/player_configs.xml"
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
                'name': 'Goal Medal',
                'index': 'goal_medal',
                'sorting': True,
                'searching': False,
                'width': 30,
                'action': self._prompt_for_goal_medal
            },
            {
                'name': 'Skip Medal',
                'index': 'skip_medal',
                'sorting': True,
                'searching': False,
                'width': 30,
                'action': self._prompt_for_skip_medal
            },
        ]

    async def get_actions(self):
        return [
            {
                    'name': 'Enabled',
                    'action': self.action_toggle_enabled_player,
                    'style': 'Icons64x64_1',
                    'substyle': 'Check',
                    'attrs_renderer': self._render_action_attr,
            },
        ]

    async def action_toggle_enabled_player(self, player, values, row, **kwargs):
        input_value = await prompt_for_input(player, f"Enable or disable player, OK for global player enabled: {self.app.app_settings.enabled}", [
            {"name": "Enable", "value": True},
            {"name": "Disable", "value": False},
        ], entry=False, validator=lambda x: (True, ""))
        self.app.app_settings.player_configs[row["player_login"]].enabled = input_value
        await self.refresh(player=player)

    async def get_data(self):
        self.app.app_settings.update_player_configs()
        return [
            {
                "player_nickname": player_config.player.nickname,
                "player_login": player_config.player.login,
                "goal_medal": player_config.goal_medal.name if player_config.goal_medal else None,
                "skip_medal": player_config.skip_medal.name if player_config.skip_medal else None,
            }
            for player_config in sorted(self.app.app_settings.player_configs.values(), key=lambda x: x.player.nickname)
        ]

    def _render_action_attr(self, row, action):
        return [
            {
                "key": "styleselected",
                "value": self.app.app_settings.player_configs[row["player_login"]].enabled if self.app.app_settings.player_configs[row["player_login"]].enabled is not None else self.app.app_settings.enabled
            }
        ]

    async def _prompt_for_goal_medal(self, player, values, row, **kwargs):
        buttons = [
            {"name": medal.name, "value": medal}
            for medal in [Medals.AUTHOR, Medals.GOLD, Medals.SILVER]
        ]

        medal = await prompt_for_input(player, f"Goal Medal, OK for global Goal Medal: {self.app.app_settings.goal_medal.name}", buttons=buttons, entry=False, validator=lambda x: (True, ""))
        self.app.app_settings.player_configs[row["player_login"]].goal_medal = medal

        await self.refresh(player=player)

    async def _prompt_for_skip_medal(self, player, values, row, **kwargs):
        buttons = [
            {"name": medal.name, "value": medal}
            for medal in [Medals.GOLD, Medals.SILVER, Medals.BRONZE]
        ]

        medal = await prompt_for_input(player, f"Skip Medal, OK for global Skip Medal: {self.app.app_settings.skip_medal.name}", buttons=buttons, entry=False, validator=lambda x: (True, ""))
        self.app.app_settings.player_configs[row["player_login"]].skip_medal = medal

        await self.refresh(player=player)

class PlayerPromptView(AlertView):
    template_name = 'random_maps_together/prompt.xml'

    def __init__(self, message, buttons=None, manager=None, default='', validator=None, entry=True):
        super().__init__(message, "md", buttons, manager)
        self.data["buttons"] = buttons or []
        self.disable_alt_menu = True
        self.entry = entry

        self.default = default
        self.validator = validator or self.validate_input

        self.data['default'] = self.default
        self.data["entry"] = self.entry

    async def wait_for_input(self):  # pragma: no cover
        """
        Wait for input and return it.
        :return: Returns the string value of the user.
        """
        return await self.response_future

    def validate_input(self, value):  # pragma: no cover
        if not value or len(value) == 0:
            return False, 'Empty value given!'
        return True, None

    async def handle(self, player, action, values, **kwargs):  # pragma: no cover
        # Try to parse the button id instead of the whole action string.
        button = None
        try:
            match = re.search(r'button_([0-9]+)$', action)
            if match:
                button = match.group(1)
            match = re.search(r'button_(ok)$', action)
            if match:
                button = match.group(1)
        except:
            pass

        if button == "ok":
            self.data['errors'] = ''
            value = self.default
            if 'prompt_value' in values:
                value = values['prompt_value']

            valid, message = self.validator(value)

            if valid:
                await self.close(player)
                self.response_future.set_result(value)
                return

            self.data['errors'] = message
        elif button:
            await self.close(player)
            self.response_future.set_result(self.data["buttons"][int(button)])
            return

        await self.display([player.login])

async def prompt_for_input(player, message, buttons=None, entry=True, validator=None, default=None):
    prompt_view = PlayerPromptView(message, buttons, entry=entry, validator=validator, default=default)
    await prompt_view.display([player])
    player_input = await prompt_view.wait_for_input()
    await prompt_view.destroy()
    if isinstance(player_input, dict):
        return player_input.get("value", player_input["name"])
    else:
        return player_input
