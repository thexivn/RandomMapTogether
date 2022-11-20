from dataclasses import dataclass


@dataclass
class GameScore:
    total_at: int = 0
    total_gold: int = 0

    def inc_at(self):
        self.total_at += 1

    def inc_gold(self):
        self.total_gold += 1

    def rest(self):
        self.total_gold = 0
        self.total_at = 0
