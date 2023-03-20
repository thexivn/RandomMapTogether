from dataclasses import dataclass
from enum import Enum
import time as py_time


class GameStage(Enum):
    HUB = 0,
    RMT = 1


@dataclass
class GameState:
    start_time = None
    stage: GameStage = GameStage.HUB
    current_map_completed: bool = False
    map_is_loading: bool = False
    free_skip_available: bool = False
    game_is_in_progress: bool = False
    skip_medal_available: bool = False
    skip_medal_player = None
    fins_count_from = "*"  # "*" for anyone, otherwise players login
    fins_count_from_name = "Anyone"

    def is_hub_stage(self) -> bool:
        return GameStage.HUB == self.stage

    def is_game_stage(self) -> bool:
        return GameStage.RMT == self.stage

    def skip_command_allowed(self):
        return self.is_game_stage() and not self.current_map_completed

    def set_start_new_state(self):
        self.start_time = py_time.time()
        self.current_map_completed = True
        self.stage = GameStage.RMT
        self.free_skip_available = True
        self.skip_medal_available = False
        self.map_is_loading = False
        self.fins_count_from = "*"
        self.fins_count_from_name = "Anyone"

    def set_new_map_in_game_state(self):
        self.current_map_completed = False
        self.game_is_in_progress = True
        self.map_is_loading = False

    def set_map_completed_state(self):
        self.current_map_completed = True
        self.skip_medal_available = False

    def set_hub_state(self):
        self.stage = GameStage.HUB
        self.game_is_in_progress = False
        self.free_skip_available = False
        self.skip_medal_available = False

    def set_finishes_player_filter(self, login: str, name: str):
        self.fins_count_from = login
        self.fins_count_from_name = name
