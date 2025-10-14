from enum import Enum
LANE_POSITION = ("Top", "Jungle", "Middle", "Bottom", "Utility")

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
    I = 1
    II = 2
    III = 3
    IV = 4
    
class LeagueQueue(Enum):
    RANKED_SOLO_5x5 = "RANKED_SOLO_5x5"
    RANKED_FLEX_SR = "RANKED_FLEX_SR"
    RANKED_FLEX_TT = "RANKED_FLEX_TT"