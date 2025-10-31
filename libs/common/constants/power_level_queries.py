GET_PLAYER_POWER_LEVELS_SQL = """
SELECT *
FROM app.power_levels
WHERE puuid = :puuid
LIMIT :limit
OFFSET :skip
"""

GET_PLAYER_MATCH_POWER_LEVEL_SQL = """
SELECT *
FROM app.power_levels
WHERE puuid = :puuid AND match_id = :match_id
"""

CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL = """
SELECT EXISTS (
  SELECT 1 FROM app.power_levels WHERE puuid = :puuid AND match_id = :match_id
) AS exists;
"""