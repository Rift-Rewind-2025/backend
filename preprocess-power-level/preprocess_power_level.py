import os, json, boto3
from dotenv import load_dotenv
from urllib.parse import unquote_plus
import posixpath
from services.power_level_service import PowerLevelService

load_dotenv()

rdsd = boto3.client("rds-data")
s3 = boto3.client("s3")
DB_ARN     = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DB_NAME    = os.environ["DB_NAME"]

power_level_service = PowerLevelService()

BOOL_KEYS_FROM_INT = {"first_blood_taken", "perfect_game"}
BOOL_KEYS_NATIVE   = {"win", "first_blood_assist"}

def normalize(m):
    m = dict(m)  # copy
    # role -> uppercase canonical
    if "role_position" in m:
        rp = str(m["role_position"]).upper()
        if rp == "MIDDLE": rp = "MID"
        m["role_position"] = rp
    # ints that should be bools
    for k in BOOL_KEYS_FROM_INT:
        if k in m:
            m[k] = bool(int(m[k]))
    # ensure native bools are real bools
    for k in BOOL_KEYS_NATIVE:
        if k in m:
            m[k] = bool(m[k])
    # drop computed fields (DB generates)
    m.pop("kda", None)
    m.pop("game_minutes", None)
    return m

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

# assemble named params for Data API
def nv(name, value):
    if value is None: return {"name": name, "value": {"isNull": True}}
    if isinstance(value, bool): return {"name": name, "value": {"booleanValue": value}}
    if isinstance(value, int):  return {"name": name, "value": {"longValue": value}}
    if isinstance(value, float):return {"name": name, "value": {"doubleValue": float(value)}}
    return {"name": name, "value": {"stringValue": str(value)}}

def insert_power_metrics(match_id: str, puuid: str, metrics: dict):
    m = normalize(metrics)

    params = [nv("match_id", match_id), nv("puuid", puuid)] + [
        nv(k, m.get(k)) for k in [
          "champion_name","role_position","champ_level",
          "game_duration","win",
          "kills","deaths","assists",
          "total_damage_dealt","total_damage_taken","damage_per_minute",
          "team_damage_percentage","damage_taken_on_team_percentage",
          "total_gold","gold_per_minute","cs_count",
          "vision_score","wards_placed","wards_destroyed","vision_score_per_minute",
          "dragons_killed","barons_killed","heralds_killed","turrets_destroyed","turret_plates_taken",
          "skillshots_hit","skillshot_accuracy","skillshots_dodged","immobilize_and_kill",
          "solo_kills","outnumbered_kills","double_kills","triple_kills","quadra_kills","penta_kills",
          "killing_sprees","largest_killing_spree","first_blood_taken","first_blood_assist",
          "kill_participation","full_team_takedowns","save_ally_from_death","pick_kill_with_ally","kill_after_hidden",
          "longest_time_living","time_spent_dead","survived_three_immobilizes","deaths_by_enemy_champs",
          "time_ccing_others","enemy_immobilizations",
          "legendary_items_count","max_level_lead","takedowns_first_10min",
          "flawless_aces","perfect_game"
        ]
    ]

    return rdsd.execute_statement(
        resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
        sql=METRICS_INSERT_SQL, parameters=params
    )
    
def insert_power_levels(match_id: str, puuid: str, power_levels: dict):
    params = [nv("match_id", match_id), nv("puuid", puuid)] + [
        nv(k, power_levels.get(k)) for k in [
          "combat", "objectives", "vision", "economy", "clutch", "total"
        ]
    ]

    return rdsd.execute_statement(
        resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
        sql=POWER_LEVEL_INSERT_SQL, parameters=params
    )

def lambda_handler(event, context):
    '''
    Main Lambda handler function to preprocess the power level and save it to Aurora RDS
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    '''
    out = []
    for rec in event.get("Records", []):
        bucket = rec['s3']['bucket']['name']
        key = unquote_plus(rec['s3']['object']['key'])
        
        # get the parent folder path which will be a puuid folder
        puuid = os.path.basename(os.path.dirname(key))
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        matches = json.loads(body)
        
        for match_json in matches:
            player_idx = match_json['metadata']['participants'].index(puuid)
            match_id = match_json['metadata']['matchId']
            
            # extract all the power level metrics from the match object
            player_metrics = power_level_service.extract_all_metrics(match_json, player_idx)
            
            insert_power_metrics(match_id, puuid, player_metrics)
            
            # get the power level calculations from the metrics
            player_power_level = power_level_service.calculate_power_level(player_metrics)
            
            insert_power_levels(match_id, puuid, player_power_level)

    return {
        "ok": True
    }
        