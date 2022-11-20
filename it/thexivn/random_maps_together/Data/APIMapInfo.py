from dataclasses import dataclass


@dataclass
class APIMapInfo:
    uuid: str
    author_time: int
    content: bytes
