from dataclasses import dataclass, field
from datetime import date
from typing import List


@dataclass
class APIMapInfo:
    uuid: str
    author_time: int
    last_update: date
    content: bytes
    tags: List[int]
