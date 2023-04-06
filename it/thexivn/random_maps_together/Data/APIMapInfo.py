from dataclasses import dataclass
from typing import Tuple

from .map_tag import MapTag
from datetime import datetime
from .Constants import TAG_BOBSLEIGH, TAG_ICE, ICE_CHANGE_DATE


@dataclass(frozen=True)
class APIMapInfo:
    TrackID: int
    TrackUID: int
    UpdatedAt: datetime
    Username: str
    Name: str
    Tags: Tuple[MapTag]

    def is_pre_patch_ice(self) -> bool:
        return (self.has_tag_id(TAG_BOBSLEIGH) or self.has_tag_id(TAG_ICE)) and self.UpdatedAt < ICE_CHANGE_DATE

    def has_tag_id(self, tag_id) -> bool:
        if next((tag for tag in self.Tags if tag.ID == tag_id), None):
            return True
        return False

    @classmethod
    def from_json(cls, json, map_tags) -> "APIMapInfo":
        date, milliseconds = json["UpdatedAt"].split(".")
        json["UpdatedAt"] = f"{date}.{int(milliseconds):<03d}"
        return cls(
            json["TrackID"],
            json["TrackUID"],
            datetime.fromisoformat(json["UpdatedAt"]).date(),
            json["Username"],
            json["Name"],
            tuple(next(map_tag for map_tag in map_tags if map_tag.ID == int(tag_id) ) for tag_id in json["Tags"].split(",")),
        )
    # "UserID": 129732,
    # "GbxMapName": "Toybox Garden",
    # "AuthorLogin": "v9utFEe5Tx6XA_axE2iU3g",
    # "MapType": "TM_Race",
    # "TitlePack": "TMStadium",
    # "TrackUID": "VxVsErO7phpDVTPVfDaYSGb6Vrf",
    # "Mood": "48x48Day",
    # "DisplayCost": 2827,
    # "ModName": "",
    # "Lightmap": 8,
    # "ExeVersion": "3.3.0",
    # "ExeBuild": "2023-03-31_13_17",
    # "AuthorTime": 55008,
    # "ParserVersion": 2,
    # "UploadedAt": "2023-04-06T10:33:33.57",
    # "UpdatedAt": "2023-04-06T10:33:33.57",
    # "TypeName": "Race",
    # "StyleName": "Fragile",
    # "EnvironmentName": "Stadium",
    # "VehicleName": "CarSport",
    # "UnlimiterRequired": False,
    # "RouteName": "Single",
    # "LengthName": "1 min",
    # "DifficultyName": "Advanced",
    # "Laps": 1,
    # "ReplayWRID": None,
    # "ReplayWRTime": None,
    # "ReplayWRUserID": None,
    # "ReplayWRUsername": None,
    # "TrackValue": 0,
    # "Comments": "Welcome to Toybox Garden! Remember to play gently with your toys, or you might just break them! Happy Hunting!",
    # "MappackID": 0,
    # "Unlisted": False,
    # "Unreleased": False,
    # "Downloadable": True,
    # "RatingVoteCount": 0,
    # "RatingVoteAverage": 0.0,
    # "HasScreenshot": False,
    # "HasThumbnail": True,
    # "HasGhostBlocks": True,
    # "EmbeddedObjectsCount": 0,
    # "EmbeddedItemsSize": 12,
    # "AuthorCount": 1,
    # "IsMP4": True,
    # "SizeWarning": False,
    # "AwardCount": 0,
    # "CommentCount": 0,
    # "ReplayCount": 0,
    # "ImageCount": 0,
    # "VideoCount": 0
