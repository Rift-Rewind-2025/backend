import logging, json, os, boto3, uuid
from botocore.exceptions import ClientError
from libs.common.constants.league_constants import LeagueTier, MATCH_V5_URL, MATCH_PUUID_V5_URL, GET_PLAYER_ACTIVE_REGION_URL, PLAYER_RANK_URL
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from datetime import datetime
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)
riot_api_service = RiotRateLimitAPI()

s3_client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        )

BUCKET = os.getenv("S3_BUCKET_NAME")

def put_json_s3(key: str, obj) -> str:
    """Write a JSON object (pretty-printed UTF-8) to S3."""
    try:
        body = json.dumps(obj, ensure_ascii=False, indent=4).encode("utf-8")
        s3_client.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=body,
            ContentType="application/json; charset=utf-8",
        )
        return f"s3://{BUCKET}/{key}"
    except ClientError:
        # re-raise after logging if you have a logger
        raise Exception("cannot")

def download_players_yearly_match_info(puuid: str, save_directory: str, count: int = 10):
    """
    Downloads the player's last-year ranked match payloads and writes them to S3 in bulks.
    S3 keys:  {prefix}/{puuid}/match_info_bulk_{n}.json
    """

    # time window: last year → now (epoch seconds)
    now_dt = datetime.now(ZoneInfo("America/Los_Angeles"))
    try:
        # TODO: limit until Jan 1st of current year
        last_year_dt = now_dt.replace(year=now_dt.year - 1)
    except ValueError:  # handle Feb 29 → Feb 28
        last_year_dt = now_dt.replace(year=now_dt.year - 1, day=28)
    start_time = int(last_year_dt.timestamp())
    end_time = int(now_dt.timestamp())

    # Get player's active region (NA1, KR, etc)
    active_region_res = riot_api_service.call_endpoint_with_rate_limit(GET_PLAYER_ACTIVE_REGION_URL.format(puuid=puuid))
    
    active_region = active_region_res['region']
    
    # Get player's current rank (we are only doing SOLO ranks to find their "actual" skills)
    player_rank_res = riot_api_service.call_endpoint_with_rate_limit(PLAYER_RANK_URL.format(region=active_region, puuid=puuid))
    
    p_tier, p_rank = player_rank_res.get('tier', "BRONZE"), player_rank_res.get('rank', 'I')
    
    start = 0
    bulk_count = 0
    s3_keys = []
    key_prefix = f"{save_directory}/{p_tier}_{f'{p_rank}_' if p_tier not in (LeagueTier.CHALLENGER.name, LeagueTier.GRANDMASTER.name, LeagueTier.MASTER.name) else ""}match_infos/{puuid}"

    while True:
        # page ranked match IDs
        match_ids_ranked = riot_api_service.call_endpoint_with_rate_limit(
            MATCH_PUUID_V5_URL.format(
                puuid=puuid, start=start, count=count,
                startTime=start_time, endTime=end_time, type='ranked'
            ),
        )
        if not match_ids_ranked:
            break

        # fetch each match object
        match_obj = []
        for match_id in match_ids_ranked:
            match_info = riot_api_service.call_endpoint_with_rate_limit(
                MATCH_V5_URL.format(match_id=match_id)
            )
            match_obj.append(match_info)

        # write bulk JSON to S3
        key = f"{key_prefix}/match_info_bulk_{bulk_count}.json"
        uri = put_json_s3(key, match_obj)
        s3_keys.append(uri)

        start += count
        bulk_count += 1
        

    return s3_keys

def lambda_handler(event, context):
    puuid = (event or {}).get("puuid")
    corr_id = str(uuid.uuid4())
    if not puuid or not isinstance(puuid, str):
        log.error("Missing/invalid 'puuid' in event")
        # For async invoke, return value is ignored; we still log for observability
        return {"ok": False, "error": "missing_puuid", "corr_id": corr_id}

    try:
        result = download_players_yearly_match_info(puuid, "rank_match_info", 50)
        log.info("DONE corr_id=%s summary=%s", corr_id, json.dumps(result)[:2000])
        return {"ok": True, "corr_id": corr_id, **result}
    except Exception as exc:
        log.exception("FAILED corr_id=%s puuid=%s", corr_id, puuid)
        return {"ok": False, "error": str(exc), "corr_id": corr_id}