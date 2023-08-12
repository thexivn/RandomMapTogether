from dataclasses import dataclass
from typing import Union
import time
import logging
from pyplanet.utils.times import format_time

logger = logging.getLogger(__name__)

@dataclass
class RoundTimer:
    total_time: int = 0
    start_round: Union[int, float] = 0
    last_round: int = 0

    def start_timer(self):
        if self.start_round:
            raise RuntimeError("Timer already started")
        self.start_round = time.time()

    def stop_timer(self):
        if not self.start_round:
            raise RuntimeError("No timer running")

        self.last_round = int(time.time() - self.start_round - 1)
        self.total_time += self.last_round
        self.start_round = 0

    @property
    def current_round(self):
        if not self.start_round:
            return 0
        return int(time.time() - self.start_round - 1)

    def __str__(self):
        return format_time(int((self.total_time + self.current_round) * 1000), hide_milliseconds=True)
