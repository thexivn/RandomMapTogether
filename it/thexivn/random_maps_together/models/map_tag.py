from dataclasses import dataclass

import re


@dataclass(frozen=True)
class MapTag:
    id: int
    name: str
    color: str

    def __str__(self):
        return f"${self.rrggbb_to_rgb()}{self.name}"

    def rrggbb_to_rgb(self):
        if not self.color:
            return "z"
        r, g, b = re.findall(r"\w{2}", self.color)
        r = round(int(r, 16) / 0xFF*0xF)
        g = round(int(g, 16) / 0xFF*0xF)
        b = round(int(b, 16) / 0xFF*0xF)
        return f"{r:x}{g:x}{b:x}"

    @classmethod
    def from_json(cls, json):
        return cls(
            json["ID"],
            json["Name"],
            json["Color"],
        )
