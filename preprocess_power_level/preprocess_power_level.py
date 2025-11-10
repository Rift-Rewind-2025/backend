import os, json, boto3, requests, logging
from dotenv import load_dotenv
from urllib.parse import unquote_plus
from libs.common.constants.queries.power_level_metrics_queries import POWER_LEVEL_METRICS_INSERT_SQL
from libs.common.constants.queries.power_level_queries import POWER_LEVEL_INSERT_SQL, GET_PLAYER_MATCH_POWER_LEVEL_COUNT
from libs.common.constants.queries.users_queries import INSERT_USER_SQL, CHECK_IF_USER_EXISTS_SQL, UPDATE_USER_AVERAGE_POWER_LEVEL_SQL, UPDATE_USER_STD_POWER_LEVEL_SQL
from libs.common.constants.queries.rank_norms_queries import REBUILD_RANK_NORMS_SQL
from libs.common.constants.league_constants import GET_NAME_BY_PUUID_URL, GET_PLAYER_ACTIVE_REGION_URL, PLAYER_RANK_URL, LeagueQueue
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from services.power_level_service import PowerLevelService

load_dotenv()

# rdsd = boto3.client("rds-data")
rds_service = RdsDataService.from_env()
s3 = boto3.client("s3")
DB_ARN     = os.environ["DB_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DB_NAME    = os.environ["DB_NAME"]
RIOT_API_KEY = os.environ["RIOT_API_KEY"]

# Logging
log = logging.getLogger(__name__)

power_level_service = PowerLevelService()

riot_api_service = RiotRateLimitAPI()

BOOL_KEYS_FROM_INT = {"first_blood_taken", "perfect_game"}
BOOL_KEYS_NATIVE   = {"win", "first_blood_assist"}

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
    
    return rds_service.exec(POWER_LEVEL_METRICS_INSERT_SQL, {**m, "match_id": match_id, "puuid": puuid})
    
def insert_power_levels(match_id: str, puuid: str, power_levels: dict):
    return rds_service.exec(POWER_LEVEL_INSERT_SQL, {**power_levels, "match_id": match_id, "puuid": puuid})

def insert_user_if_not_exists(puuid: str):
    row = rds_service.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": puuid})
    print(row)
    if not bool(row['exists']):
        # user doesn't exist, add to DB
        # first, get the game_name and tag_line from RIOT API
        player = riot_api_service.call_endpoint_with_rate_limit(GET_NAME_BY_PUUID_URL.format(puuid=puuid))
        
        game_name = player['gameName']
        tag_line = player['tagLine']
        
        # Get player's active region (NA1, KR, etc)
        active_region_res = riot_api_service.call_endpoint_with_rate_limit(GET_PLAYER_ACTIVE_REGION_URL.format(puuid=puuid))
        
        active_region = active_region_res['region']
        
        # Get player's current rank (we are only doing SOLO ranks to find their "actual" skills)
        player_rank_res = riot_api_service.call_endpoint_with_rate_limit(PLAYER_RANK_URL.format(region=active_region, puuid=puuid))
        
        player_rank = next((d for d in player_rank_res if d.get("queueType") == LeagueQueue.RANKED_SOLO_5x5.value), {})
        
        p_tier, p_rank = player_rank.get('tier', "GOLD"), player_rank.get('rank', 'I')
        
        rds_service.exec(INSERT_USER_SQL, {"puuid": puuid, "game_name": game_name, "tag_line": tag_line, "real_rank_tier": p_tier, "real_rank_division": p_rank})

def get_player_match_power_level_count(puuid: str):
    row = rds_service.query_one(GET_PLAYER_MATCH_POWER_LEVEL_COUNT, {"puuid": puuid})
    return int(row['count'])

def calculate_user_avg_power_level(puuid: str):
    return rds_service.exec(UPDATE_USER_AVERAGE_POWER_LEVEL_SQL, {"puuid": puuid})

def calculate_user_std_power_level(puuid: str):
    return rds_service.exec(UPDATE_USER_STD_POWER_LEVEL_SQL, {"puuid": puuid})
        
def rebuild_rank_norms():
    return rds_service.exec(REBUILD_RANK_NORMS_SQL)

def lambda_handler(event, context):
    '''
    Main Lambda handler function to preprocess the power level and save it to Aurora RDS
    Parameters:
        event: Dict containing the Lambda function event data
        context: Lambda runtime context
    '''
    
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
        
        log.info(f'User PUUID#{puuid} inserted!')
        
        for match_json in matches:
            player_idx = match_json['metadata']['participants'].index(puuid)
            match_id = match_json['metadata']['matchId']
            
            # extract all the power level metrics from the match object
            player_metrics = power_level_service.extract_all_metrics(match_json, player_idx)
            
            insert_power_metrics(match_id, puuid, player_metrics)
            
            log.info(f'Power level metrics for PUUID#{puuid} inserted!')
            
            # get the power level calculations from the metrics
            player_power_level = power_level_service.calculate_power_level(player_metrics)
            
            insert_power_levels(match_id, puuid, player_power_level)
            
            log.info(f'Power level for PUUID#{puuid} inserted!')
            
            # check if there are already 200 power level matches
            if get_player_match_power_level_count(puuid) == 200:
                # calculate avg power level
                calculate_user_avg_power_level(puuid)
                # rebuild rank norms
                rebuild_rank_norms()
                # update the user's standardized power level
                calculate_user_std_power_level(puuid)
                
                
            
        # if it does, calculate user's average power level   
        calculate_user_avg_power_level(puuid)
        
        # at the end, rebuild rank norms after averaging user's power level
        rebuild_rank_norms()
        
        # now, after rebuilding the rank normalizations, we update the standardized power level
        calculate_user_std_power_level(puuid)

    return {
        "ok": True
    }
        