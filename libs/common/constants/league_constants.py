from enum import Enum

MAP_WIDTH = 16000
MAP_HEIGHT = 16000

LANE_POSITION = ("Top", "Jungle", "Middle", "Bottom", "Utility")

class RolePosition(str, Enum):
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"
    UTILITY = "UTILITY"

class LeagueTier(Enum):
    IRON = "iron"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    EMERALD = "emerald"
    DIAMOND = "diamond"
    # each rank below will have their own endpoint in LEAGUE-V4 API
    MASTER = "master"
    GRANDMASTER = "grandmaster"
    CHALLENGER = "challenger"
    
class LeagueDivision(Enum):
    I = 'I'
    II = 'II'
    III = 'III'
    IV = 'IV'
    
class LeagueQueue(Enum):
    RANKED_SOLO_5x5 = "RANKED_SOLO_5x5"
    RANKED_FLEX_SR = "RANKED_FLEX_SR"
    RANKED_FLEX_TT = "RANKED_FLEX_TT"