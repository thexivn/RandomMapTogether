from dataclasses import dataclass
import time as py_time


@dataclass
class GameState:
    start_time = None
    map_start_time = None
    current_map_completed: bool = True
    free_skip_available: bool = True
    skip_medal_player = None
    skip_medal = None
    is_paused = False

    def map_played_time(self):
        if self.current_map_completed:
            return 0
        return int(py_time.time() - self.map_start_time - 1)
