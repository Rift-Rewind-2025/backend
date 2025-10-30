METRICS_INSERT_SQL = """
INSERT INTO app.power_level_metrics (
  match_id, puuid,
  champion_name, role_position, champ_level,
  game_duration, win,
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
  :game_duration, :win,
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
  champion_name = EXCLUDED.champion_name,
  role_position = EXCLUDED.role_position,
  champ_level   = EXCLUDED.champ_level,
  game_duration = EXCLUDED.game_duration,
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

POWER_LEVEL_INSERT_SQL = """
INSERT INTO app.power_levels (
  match_id, puuid,
  combat, objectives, vision, economy, clutch, total
) VALUES (
  :match_id, :puuid,
  :combat, :objectives, :vision, :economy, :clutch, :total
)
ON CONFLICT (match_id, puuid) DO UPDATE SET
  combat     = EXCLUDED.combat,
  objectives = EXCLUDED.objectives,
  vision     = EXCLUDED.vision,
  economy    = EXCLUDED.economy,
  clutch     = EXCLUDED.clutch,
  total      = EXCLUDED.total;
"""

CHECK_IF_USER_EXISTS_SQL = """
SELECT EXISTS (
  SELECT 1 FROM app.users WHERE puuid = :puuid
) AS exists;
"""