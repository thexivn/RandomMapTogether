from dataclasses import dataclass

import re


@dataclass(frozen=True)
class MapTag:
    ID: int
    Name: str
    Color: str

    def __str__(self):
        return f"${self.rrggbb_to_rgb()}{self.Name}"

    def rrggbb_to_rgb(self):
        if not self.Color:
            return "z"
        r, g, b = re.findall(r"\w{2}", self.Color)
        r = round(int(r, 16) / 0xFF*0xF)
        g = round(int(g, 16) / 0xFF*0xF)
        b = round(int(b, 16) / 0xFF*0xF)
        return f"{r:x}{g:x}{b:x}"
