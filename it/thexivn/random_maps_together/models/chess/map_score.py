from dataclasses import dataclass
from ..enums.team import Team

@dataclass
class MapScore:
    map_points: int
    name: str
    team: Team
    match_points: int
    round_points: int

    @classmethod
    def from_json(cls, json):
        return cls(
            map_points=json["map_points"],
            name=json["name"],
            team=Team(json["id"]),
            match_points=json["match_points"],
            round_points=json["round_points"],
        )
