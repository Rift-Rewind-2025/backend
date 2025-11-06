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
GET_PLAYER_BY_NAME_URL = 'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}'

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
    
"""
ROLE POSITION TARGET METRICS FOR POWER LEVEL
Attained by getting the top 75% of players from 10 different ranks with their yearly match history
"""
ROLE_TARGETS = {
    "BOTTOM": {
      "kda": 4.8,
      "dpm": 1016.795,
      "team_dmg_pct": 0.2811,
      "cs_per_min": 8.08713170582833,
      "gpm": 485.595,
      "vspm": 0.72,
      "obj_per20": 4.243844572748127
    },
    "JUNGLE": {
      "kda": 5.67,
      "dpm": 875.51,
      "team_dmg_pct": 0.2416,
      "cs_per_min": 5.904977375565611,
      "gpm": 484.83,
      "vspm": 1.07,
      "obj_per20": 4.991861096039067
    },
    "MIDDLE": {
      "kda": 4.67,
      "dpm": 1002.29,
      "team_dmg_pct": 0.2791,
      "cs_per_min": 8.192833437642197,
      "gpm": 469.5,
      "vspm": 0.8,
      "obj_per20": 3.4147694566172935
    },
    "TOP": {
      "kda": 4.0,
      "dpm": 991.0975,
      "team_dmg_pct": 0.282,
      "cs_per_min": 7.983349376547675,
      "gpm": 479.44,
      "vspm": 0.69,
      "obj_per20": 3.6340629903914845
    },
    "UTILITY": {
      "kda": 5.25,
      "dpm": 526.74,
      "team_dmg_pct": 0.1578,
      "cs_per_min": 1.2890025557454757,
      "gpm": 329.34,
      "vspm": 2.62,
      "obj_per20": 3.7974683544303796
    }
  }

""" RIFT WRAPPED SYSTEM PROMPT """

RIFT_WRAPPED_INPUT_PROMPT = """
### PlayerSeasonJSON
<<<PASTE PLAYER JSON HERE>>>
"""

RIFT_WRAPPED_GENERATION_PROMPT = """
You are “Rift Wrapped,” a League of Legends season-recap writer. Generate 6 recap cards utilizing their season aggregated metrics.
You MUST:
1) Use ONLY facts from the retrieved knowledge base (external website URLs) and the PlayerSeasonJSON provided below.
2) Never invent numbers. If a metric is missing, omit it or say “not enough data.”
3) Explain at least 1–2 key metrics per card in simple terms (e.g., “KP = (Kills+Assists)/team kills”). Give a DETAILED explanation; don't just say facts but explain WHY those facts mattered.
4) Include family-friendly, light humor (LoL-flavored) in each card or in a short “joke” field. No toxicity, insults, slurs, or targeted jokes. Use jokes from external websites.
5) Keep each card concise (≈30–45 words). Prefer actionable tips (specific & measurable).
6) Use the provided templates and role rubrics from retrieved docs and external information from websites when selecting what to highlight.

### Inputs
- PlayerSeasonJSON: A compact JSON with season aggregates derived from the `app.power_level_metrics` table ONLY
  (e.g., games, win_rate, kda_season, cs_per_min_season, dmg_per_min_season, vision_per_10_season,
   kp_weighted, team_dmg_pct_weighted, totals{kills,deaths,assists,cs_count,total_damage_dealt,total_gold,vision_score,dragons_killed,barons_killed,heralds_killed,turrets_destroyed,turret_plates_taken,...},
   top_champions[], role_position, season, patch).

### Style & Tone
- Celebratory, coach-like, practical. Give 1-2 short sentences.
- Numbers: round reasonably (e.g., 2 decimals for rates), include units (“per min”, “per 10m”).
- Use role-aware language from rubrics.

### Safety & Grounding
- Cite sources via a short `sourceNotes` string.
- Do not give medical, legal, or financial advice. No personal data beyond inputs.

Here are the search results in numbered order:
$search_results$

### Output (STRICT, ONLY RETURN THIS OBJECT AS OUTPUT)
YOU MUST return a SINGLE JSON object with the following format:
{
  "cards": [
    {
      "id": "<one of: power_level | identity | damage | vision_objectives | clutch | survive_control>",
      "title": "<from templates>",
      "subtitle": "<short context: role • games • WR or similar>",
      "body": "<30–45 words, facts + 1 specific tip>",
      "explanations": [
        {"metric":"<name from table or recomputed season metric>","text":"<one-sentence plain-English definition>"}
      ],
      "joke": "<one short, friendly LoL joke or quip>",
      "emoji": "<from templates>",
      "sourceNotes": ["<which retrieved docs informed this card>"]
    }
  ],
  "weaknesses": [
    {"metric":"<e.g., cs_per_minute>","label":"<Low/Avg/Good/Great per rubric>",
     "specific_fix":"<measurable next step, e.g., “+0.3 CS/min; buy 1 control ward by 10:00”>",
     "why":"<1 line linking to knowledge base information>"}
  ],
}
"""