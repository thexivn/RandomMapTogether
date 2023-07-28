from dataclasses import dataclass
from ...enums.team import Team

@dataclass
class Piece:
    team: Team
    x: int
    y: int
    max_steps: None
    captured: bool = False
