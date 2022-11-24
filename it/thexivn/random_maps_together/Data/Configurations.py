from dataclasses import dataclass

from it.thexivn.random_maps_together.Data.Constants import SILVER, BRONZE


@dataclass
class Configurations:
    game_time_seconds = 3600
    AT_time = SILVER
    GOLD_time = BRONZE

    def set_game_time(self, old_value: str, seconds: str):
        if int(seconds) < 300:
            self.game_time_seconds = 300
        else:
            self.game_time_seconds = seconds

    def set_at_time(self, old_value: str, value: str):
        self.AT_time = value

    def set_gold_time(self, old_value: str, value: str):
        self.GOLD_time = value
