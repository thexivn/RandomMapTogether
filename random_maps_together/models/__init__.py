"""
random_maps_together Models.
"""
from .database.rmt.random_maps_together_score import RandomMapsTogetherScore
from .database.rmt.random_maps_together_player_score import RandomMapsTogetherPlayerScore

__all__ = [
    "RandomMapsTogetherScore",
    "RandomMapsTogetherPlayerScore"
]
