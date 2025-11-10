GET_ALL_USERS_SQL = '''
SELECT *
FROM app.users
ORDER BY id ASC
LIMIT :limit
OFFSET :skip
'''

GET_ALL_USERS_RANKED_SQL = '''
SELECT *
FROM app.users
ORDER BY power_level_std DESC
LIMIT :limit
OFFSET :skip
'''

GET_USER_SQL = '''
SELECT *
FROM app.users
WHERE puuid = :puuid
'''

INSERT_USER_SQL = """
INSERT INTO app.users (
    puuid, game_name, tag_line, real_rank_tier, real_rank_division
) VALUES (
  :puuid, :game_name, :tag_line, :real_rank_tier, :real_rank_division
)
"""

CHECK_IF_USER_EXISTS_SQL = """
SELECT EXISTS (
  SELECT 1 FROM app.users WHERE puuid = :puuid
) AS exists;
"""

UPDATE_USER_SQL = """
UPDATE app.users
SET game_name = COALESCE(:game_name, game_name),
    tag_line  = COALESCE(:tag_line,  tag_line),
    updated_at = now()
WHERE puuid = :puuid
RETURNING id, puuid, game_name, tag_line, updated_at;
"""

UPDATE_USER_AVERAGE_POWER_LEVEL_SQL = """
UPDATE app.users u
SET power_level = COALESCE(pl.avg_total, 0)
FROM (
  SELECT AVG(total)::double precision AS avg_total
  FROM app.power_levels
  WHERE puuid = :puuid
) pl
WHERE u.puuid = :puuid
RETURNING u.puuid, u.power_level;
"""

UPDATE_USER_STD_POWER_LEVEL_SQL = """
UPDATE app.users u
SET power_level_std = 10000 * rn.k_rank *
                      GREATEST( LEAST( (u.power_level - rn.p10) / NULLIF(rn.p95 - rn.p10, 0), 1), 0 )
FROM app.rank_norms rn
WHERE u.puuid = :puuid
  AND rn.real_rank_tier = u.real_rank_tier
  AND rn.real_rank_division = u.real_rank_division
RETURNING u.power_level_std;
"""