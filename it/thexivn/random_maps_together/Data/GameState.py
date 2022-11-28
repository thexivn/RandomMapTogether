from dataclasses import dataclass
from enum import Enum


class GameStage(Enum):
    HUB = 0,
    RMT = 1


@dataclass
class GameState:
    stage: GameStage = GameStage.HUB
    current_map_completed: bool = False
    map_is_loading: bool = False
    free_skip_available: bool = False
    gold_skip_available: bool = False
    game_is_in_progress: bool = False

    def is_hub_stage(self) -> bool:
        return GameStage.HUB == self.stage

    def is_game_stage(self) -> bool:
        return GameStage.RMT == self.stage

    def skip_command_allowed(self):
        return self.is_game_stage() and not self.current_map_completed

    def set_start_new_state(self):
        self.current_map_completed = True
        self.stage = GameStage.RMT
        self.free_skip_available = True
        self.gold_skip_available = False

    def set_new_map_in_game_state(self):
        self.current_map_completed = False
        self.free_skip_available = False
        self.game_is_in_progress = True

    def set_map_completed_state(self):
        self.current_map_completed = True
        self.gold_skip_available = False

    def set_hub_state(self):
        self.stage = GameStage.HUB
        self.game_is_in_progress = False
        self.set_all_skip(False)

    def set_all_skip(self, available: bool):
        self.free_skip_available = available
        self.gold_skip_available = available

