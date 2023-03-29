from enum import Enum

class Medals(Enum):
    AUTHOR = "AUTHOR"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"

def medal_to_int(m: Medals):
    if m == Medals.AUTHOR: return 0
    if m == Medals.GOLD: return 1
    if m == Medals.SILVER: return 2
    if m == Medals.BRONZE: return 3
    return 3

def int_to_medal(m: int):
    if m <= 0: return Medals.AUTHOR
    if m <= 1: return Medals.GOLD
    if m <= 2: return Medals.SILVER
    return Medals.BRONZE

def min_medal(m1: Medals, m2: Medals):
    return int_to_medal(min(medal_to_int(m1) - 1, medal_to_int(m2)))

def max_medal(m1: Medals, m2: Medals):
    return int_to_medal(max(medal_to_int(m1) + 1, medal_to_int(m2)))
