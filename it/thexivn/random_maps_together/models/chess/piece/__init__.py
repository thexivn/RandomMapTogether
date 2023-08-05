from dataclasses import dataclass
from typing import Optional

from ...enums.team import Team

@dataclass
class Piece:
    team: Team
    x: int
    y: int
    max_steps: Optional[int] = None
    captured: bool = False
