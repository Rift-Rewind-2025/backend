from enum import Enum

MAP_WIDTH = 16000
MAP_HEIGHT = 16000

LANE_POSITION = ("Top", "Jungle", "Middle", "Bottom", "Utility")

# Riot API URLs
MATCH_PUUID_V5_URL = 'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&startTime={startTime}&endTime={endTime}&type={type}'
MATCH_V5_URL = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
MATCH_V5_INFO_URL = 'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/info'
PLAYER_RANK_URL = 'https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}'
GET_PLAYER_ACTIVE_REGION_URL = 'https://americas.api.riotgames.com/riot/account/v1/region/by-game/lol/by-puuid/{puuid}'
GET_NAME_BY_PUUID_URL = 'https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}'

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