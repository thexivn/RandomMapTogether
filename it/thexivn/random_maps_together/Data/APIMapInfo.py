from dataclasses import dataclass
from datetime import date, datetime
from typing import List


@dataclass
class APIMapInfo:
    uuid: str
    author_time: int
    last_update: date
    content: bytes
    tags: List[int]

    def __post_init__(self):
        self.convert_last_update()
        self.convert_to_tag_list()

    def convert_last_update(self):
        count = len(self.last_update.split('.')[-1])
        if count < 3:
            self.last_update += '0' * (3 - count)

        self.last_update = datetime.fromisoformat(self.last_update).date()

    def convert_to_tag_list(self):
        self.tags = [int(tag) for tag in self.tags.split(',')]
