from dataclasses import dataclass

@dataclass(frozen=True)
class APIMapPackInfo:
    id: int
    name: str
    downloads: int
    track_count: int

    @classmethod
    def from_json(cls, json):
        return cls(
            json["ID"],
            json["Name"],
            json["Downloads"],
            json["TrackCount"]
        )
