from dataclasses import dataclass

from .Constants import SILVER, BRONZE


@dataclass
class Configurations:
    game_time_seconds = 3600
    AT_time = SILVER
    GOLD_time = BRONZE
    min_level_to_start = 1
    infinite_free_skips = False

    def set_game_time(self, old_value: str, seconds: str):
        if int(seconds) < 300:
            self.game_time_seconds = 300
        else:
            self.game_time_seconds = int(seconds)

    def set_at_time(self, old_value: str, value: str):
        self.AT_time = value

    def set_gold_time(self, old_value: str, value: str):
        self.GOLD_time = value

    def set_min_level_to_start(self, old_value: str, value: str):
        level = int(value)
        if level < 0:
            level = 0
        elif level > 3:
            level = 3

        self.min_level_to_start = level

    def set_infinite_free_skips(self, old_value: bool, value: bool):
        self.infinite_free_skips = value
