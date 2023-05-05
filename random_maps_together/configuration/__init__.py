from dataclasses import dataclass
from pyplanet.apps import AppConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import RandomMapsTogetherApp

@dataclass
class Configuration:
    app: "RandomMapsTogetherApp"

    def can_skip_map(self):
        pass
