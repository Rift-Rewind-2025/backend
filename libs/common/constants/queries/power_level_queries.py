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

POWER_LEVEL_INSERT_SQL = """
INSERT INTO app.power_levels (
  match_id, puuid,
  combat, objectives, vision, economy, clutch, total
) VALUES (
  :match_id, :puuid,
  :combat, :objectives, :vision, :economy, :clutch, :total
)
ON CONFLICT (match_id, puuid) DO UPDATE SET
  updated_at = now(),
  combat     = EXCLUDED.combat,
  objectives = EXCLUDED.objectives,
  vision     = EXCLUDED.vision,
  economy    = EXCLUDED.economy,
  clutch     = EXCLUDED.clutch,
  total      = EXCLUDED.total;
"""

GET_PLAYER_MATCH_POWER_LEVEL_COUNT = """
SELECT COUNT(match_id) as count
FROM app.power_levels
WHERE puuid = :puuid
"""