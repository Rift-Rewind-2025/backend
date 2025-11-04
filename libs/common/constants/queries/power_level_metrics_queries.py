GET_PLAYER_POWER_LEVEL_METRICS_SQL = """
SELECT *
FROM app.power_level_metrics
WHERE puuid = :puuid
LIMIT :limit
OFFSET :skip
"""

GET_PLAYER_MATCH_POWER_LEVEL_METRICS_SQL = """
SELECT *
FROM app.power_level_metrics
WHERE puuid = :puuid AND match_id = :match_id
"""

CHECK_IF_MATCH_POWER_LEVEL_METRICS_EXISTS_SQL = """
SELECT EXISTS (
  SELECT 1 FROM app.power_level_metrics WHERE puuid = :puuid AND match_id = :match_id
) AS exists;
"""

POWER_LEVEL_METRICS_INSERT_SQL = """
INSERT INTO app.power_level_metrics (
  match_id, puuid,
  champion_name, role_position, champ_level,
  game_duration, game_start_time, win,
  kills, deaths, assists,
  total_damage_dealt, total_damage_taken, damage_per_minute,
  team_damage_percentage, damage_taken_on_team_percentage,
  total_gold, gold_per_minute, cs_count,
  vision_score, wards_placed, wards_destroyed, vision_score_per_minute,
  dragons_killed, barons_killed, heralds_killed, turrets_destroyed, turret_plates_taken,
  skillshots_hit, skillshot_accuracy, skillshots_dodged, immobilize_and_kill,
  solo_kills, outnumbered_kills, double_kills, triple_kills, quadra_kills, penta_kills,
  killing_sprees, largest_killing_spree, first_blood_taken, first_blood_assist,
  kill_participation, full_team_takedowns, save_ally_from_death, pick_kill_with_ally, kill_after_hidden,
  longest_time_living, time_spent_dead, survived_three_immobilizes, deaths_by_enemy_champs,
  time_ccing_others, enemy_immobilizations,
  legendary_items_count, max_level_lead, takedowns_first_10min,
  flawless_aces, perfect_game
) VALUES (
  :match_id, :puuid,
  :champion_name, :role_position, :champ_level,
  :game_duration, to_timestamp(:game_start_time), :win,
  :kills, :deaths, :assists,
  :total_damage_dealt, :total_damage_taken, :damage_per_minute,
  :team_damage_percentage, :damage_taken_on_team_percentage,
  :total_gold, :gold_per_minute, :cs_count,
  :vision_score, :wards_placed, :wards_destroyed, :vision_score_per_minute,
  :dragons_killed, :barons_killed, :heralds_killed, :turrets_destroyed, :turret_plates_taken,
  :skillshots_hit, :skillshot_accuracy, :skillshots_dodged, :immobilize_and_kill,
  :solo_kills, :outnumbered_kills, :double_kills, :triple_kills, :quadra_kills, :penta_kills,
  :killing_sprees, :largest_killing_spree, :first_blood_taken, :first_blood_assist,
  :kill_participation, :full_team_takedowns, :save_ally_from_death, :pick_kill_with_ally, :kill_after_hidden,
  :longest_time_living, :time_spent_dead, :survived_three_immobilizes, :deaths_by_enemy_champs,
  :time_ccing_others, :enemy_immobilizations,
  :legendary_items_count, :max_level_lead, :takedowns_first_10min,
  :flawless_aces, :perfect_game
)
ON CONFLICT (match_id, puuid) DO UPDATE SET
  updated_at = now(),
  champion_name = EXCLUDED.champion_name,
  role_position = EXCLUDED.role_position,
  champ_level   = EXCLUDED.champ_level,
  game_duration = EXCLUDED.game_duration,
  game_start_time = EXCLUDED.game_start_time,
  win           = EXCLUDED.win,
  kills         = EXCLUDED.kills,
  deaths        = EXCLUDED.deaths,
  assists       = EXCLUDED.assists,
  total_damage_dealt  = EXCLUDED.total_damage_dealt,
  total_damage_taken  = EXCLUDED.total_damage_taken,
  damage_per_minute   = EXCLUDED.damage_per_minute,
  team_damage_percentage          = EXCLUDED.team_damage_percentage,
  damage_taken_on_team_percentage = EXCLUDED.damage_taken_on_team_percentage,
  total_gold      = EXCLUDED.total_gold,
  gold_per_minute = EXCLUDED.gold_per_minute,
  cs_count        = EXCLUDED.cs_count,
  vision_score            = EXCLUDED.vision_score,
  wards_placed            = EXCLUDED.wards_placed,
  wards_destroyed         = EXCLUDED.wards_destroyed,
  vision_score_per_minute = EXCLUDED.vision_score_per_minute,
  dragons_killed      = EXCLUDED.dragons_killed,
  barons_killed       = EXCLUDED.barons_killed,
  heralds_killed      = EXCLUDED.heralds_killed,
  turrets_destroyed   = EXCLUDED.turrets_destroyed,
  turret_plates_taken = EXCLUDED.turret_plates_taken,
  skillshots_hit      = EXCLUDED.skillshots_hit,
  skillshot_accuracy  = EXCLUDED.skillshot_accuracy,
  skillshots_dodged   = EXCLUDED.skillshots_dodged,
  immobilize_and_kill = EXCLUDED.immobilize_and_kill,
  solo_kills            = EXCLUDED.solo_kills,
  outnumbered_kills     = EXCLUDED.outnumbered_kills,
  double_kills          = EXCLUDED.double_kills,
  triple_kills          = EXCLUDED.triple_kills,
  quadra_kills          = EXCLUDED.quadra_kills,
  penta_kills           = EXCLUDED.penta_kills,
  killing_sprees        = EXCLUDED.killing_sprees,
  largest_killing_spree = EXCLUDED.largest_killing_spree,
  first_blood_taken     = EXCLUDED.first_blood_taken,
  first_blood_assist    = EXCLUDED.first_blood_assist,
  kill_participation    = EXCLUDED.kill_participation,
  full_team_takedowns   = EXCLUDED.full_team_takedowns,
  save_ally_from_death  = EXCLUDED.save_ally_from_death,
  pick_kill_with_ally   = EXCLUDED.pick_kill_with_ally,
  kill_after_hidden     = EXCLUDED.kill_after_hidden,
  longest_time_living      = EXCLUDED.longest_time_living,
  time_spent_dead          = EXCLUDED.time_spent_dead,
  survived_three_immobilizes = EXCLUDED.survived_three_immobilizes,
  deaths_by_enemy_champs   = EXCLUDED.deaths_by_enemy_champs,
  time_ccing_others     = EXCLUDED.time_ccing_others,
  enemy_immobilizations = EXCLUDED.enemy_immobilizations,
  legendary_items_count = EXCLUDED.legendary_items_count,
  max_level_lead        = EXCLUDED.max_level_lead,
  takedowns_first_10min = EXCLUDED.takedowns_first_10min,
  flawless_aces         = EXCLUDED.flawless_aces,
  perfect_game          = EXCLUDED.perfect_game;
"""

GET_AGGREGATED_YEARLY_METRICS_SQL = """
WITH base AS (
  SELECT *
  FROM app.power_level_metrics
  WHERE puuid = :puuid
    AND created_at >= :start_ts
    AND created_at <  :end_ts
),
acc AS (
  SELECT
    COUNT(*) AS games,
    SUM(game_duration)                      AS secs_played,
    SUM(kills)                              AS kills,
    SUM(deaths)                             AS deaths,
    SUM(assists)                            AS assists,
    SUM(cs_count)                           AS cs_total,
    SUM(total_gold)                         AS gold_total,
    SUM(total_damage_dealt)                 AS dmg_total,        -- ideally damage to champs
    SUM(total_damage_taken)                 AS dmg_taken_total,
    SUM(vision_score)                       AS vision_total,
    SUM(dragons_killed)                     AS dragons,
    SUM(barons_killed)                      AS barons,
    SUM(turrets_destroyed)                  AS towers,
    SUM(turret_plates_taken)                AS plates,
    MAX(longest_time_living)                AS longest_living,

    -- Optional weighted sums for ratios if you have them:
    SUM(kill_participation * (kills + assists)) AS kp_weight,    -- proxy weighting
    SUM(team_damage_percentage * total_damage_dealt) AS tdp_weight
  FROM base
)
SELECT
  games,
  secs_played,
  -- Recomputed season rates
  ROUND( (kills + assists)::numeric / GREATEST(deaths,1), 2 )           AS kda_season,
  ROUND( cs_total::numeric / NULLIF(secs_played/60.0,0), 2 )            AS cs_per_min_season,
  ROUND( gold_total::numeric / NULLIF(secs_played/60.0,0), 2 )          AS gpm_season,
  ROUND( dmg_total::numeric  / NULLIF(secs_played/60.0,0), 2 )          AS dpm_season,
  ROUND( (vision_total::numeric / 10.0) / NULLIF(secs_played/60.0,0),2) AS vision_per_10_season,
  dragons, barons, towers, plates,
  longest_living,
  -- Approximations if you don't store team totals:
  ROUND( kp_weight / NULLIF(SUM(kills + assists) OVER (),0), 4 )        AS kp_weighted_approx,
  ROUND( tdp_weight / NULLIF(dmg_total,0), 4 )                          AS team_dmg_pct_weighted_approx
FROM acc;
"""