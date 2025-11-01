import os, json, boto3, requests
from dotenv import load_dotenv
from urllib.parse import unquote_plus
from libs.common.constants.queries.power_level_metrics_queries import POWER_LEVEL_METRICS_INSERT_SQL
from libs.common.constants.queries.power_level_queries import POWER_LEVEL_INSERT_SQL
from libs.common.constants.queries.users_queries import INSERT_USER_SQL, CHECK_IF_USER_EXISTS_SQL
from libs.common.rds_service import RdsDataService
from services.power_level_service import PowerLevelService

load_dotenv()

# rdsd = boto3.client("rds-data")
rds_service = RdsDataService.from_env()
s3 = boto3.client("s3")
DB_ARN     = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DB_NAME    = os.environ["DB_NAME"]
RIOT_API_KEY = os.environ["RIOT_API_KEY"]

power_level_service = PowerLevelService()

BOOL_KEYS_FROM_INT = {"first_blood_taken", "perfect_game"}
BOOL_KEYS_NATIVE   = {"win", "first_blood_assist"}

GET_NAME_BY_PUUID_URL = 'https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}'

def normalize(m):
    m = dict(m)  # copy
    # role -> uppercase canonical
    if "role_position" in m:
        rp = str(m["role_position"]).upper()
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

# assemble named params for Data API
def nv(name, value):
    if value is None: return {"name": name, "value": {"isNull": True}}
    if isinstance(value, bool): return {"name": name, "value": {"booleanValue": value}}
    if isinstance(value, int):  return {"name": name, "value": {"longValue": value}}
    if isinstance(value, float):return {"name": name, "value": {"doubleValue": float(value)}}
    return {"name": name, "value": {"stringValue": str(value)}}

def insert_power_metrics(match_id: str, puuid: str, metrics: dict):
    m = normalize(metrics)

    # params = [nv("match_id", match_id), nv("puuid", puuid)] + [
    #     nv(k, m.get(k)) for k in [
    #       "champion_name","role_position","champ_level",
    #       "game_duration","win",
    #       "kills","deaths","assists",
    #       "total_damage_dealt","total_damage_taken","damage_per_minute",
    #       "team_damage_percentage","damage_taken_on_team_percentage",
    #       "total_gold","gold_per_minute","cs_count",
    #       "vision_score","wards_placed","wards_destroyed","vision_score_per_minute",
    #       "dragons_killed","barons_killed","heralds_killed","turrets_destroyed","turret_plates_taken",
    #       "skillshots_hit","skillshot_accuracy","skillshots_dodged","immobilize_and_kill",
    #       "solo_kills","outnumbered_kills","double_kills","triple_kills","quadra_kills","penta_kills",
    #       "killing_sprees","largest_killing_spree","first_blood_taken","first_blood_assist",
    #       "kill_participation","full_team_takedowns","save_ally_from_death","pick_kill_with_ally","kill_after_hidden",
    #       "longest_time_living","time_spent_dead","survived_three_immobilizes","deaths_by_enemy_champs",
    #       "time_ccing_others","enemy_immobilizations",
    #       "legendary_items_count","max_level_lead","takedowns_first_10min",
    #       "flawless_aces","perfect_game"
    #     ]
    # ]

    # return rdsd.execute_statement(
    #     resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
    #     sql=METRICS_INSERT_SQL, parameters=params
    # )
    
    return rds_service.exec(POWER_LEVEL_METRICS_INSERT_SQL, {**metrics, "match_id": match_id, "puuid": puuid})
    
def insert_power_levels(match_id: str, puuid: str, power_levels: dict):
    # params = [nv("match_id", match_id), nv("puuid", puuid)] + [
    #     nv(k, power_levels.get(k)) for k in [
    #       "combat", "objectives", "vision", "economy", "clutch", "total"
    #     ]
    # ]

    # return rdsd.execute_statement(
    #     resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
    #     sql=POWER_LEVEL_INSERT_SQL, parameters=params
    # )
    return rds_service.exec(POWER_LEVEL_INSERT_SQL, {**power_levels, "match_id": match_id, "puuid": puuid})

def insert_user_if_not_exists(puuid: str):
    # check if user exists in DB
    # resp = rdsd.execute_statement(
    #     resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
    #     sql=CHECK_IF_USER_EXISTS_SQL, parameters=[{"name": "puuid", "value": {"stringValue": puuid}}]
    # )
    row = rds_service.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": puuid})
    print(row)
    if not bool(row['exists']):
        # user doesn't exist, add to DB
        # first, get the game_name and tag_line from RIOT API
        res = requests.get(GET_NAME_BY_PUUID_URL.format(puuid=puuid), headers={
            "X-Riot-Token": RIOT_API_KEY,
        })
        res.raise_for_status()
        player = res.json()
        game_name = player['gameName']
        tag_line = player['tagLine']
        # rdsd.execute_statement(
        #     resourceArn=DB_ARN, secretArn=SECRET_ARN, database=DB_NAME,
        #     sql=USER_INSERT_SQL, parameters=[{"name": "puuid", "value": {"stringValue": puuid}}, 
        #                                         {"name": "game_name", "value": {"stringValue": game_name}},
        #                                         {"name": "tag_line", "value": {"stringValue": tag_line}},]
        # )
        rds_service.exec(INSERT_USER_SQL, {"puuid": puuid, "game_name": game_name, "tag_line": tag_line})

        


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
        
        print(bucket, key, puuid)
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        matches = json.loads(body)
        
        # check to see if the user already exists in DB, if it doesn't create a new user in DB
        insert_user_if_not_exists(puuid)
        
        
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
        