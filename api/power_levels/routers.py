from fastapi import APIRouter, Path, Query, Depends, HTTPException, status
from typing import Annotated
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from libs.common.constants.queries.power_level_queries import GET_PLAYER_MATCH_POWER_LEVEL_SQL, GET_PLAYER_POWER_LEVELS_SQL, CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL, POWER_LEVEL_INSERT_SQL
from libs.common.constants.queries.power_level_metrics_queries import GET_AGGREGATED_YEARLY_METRICS_SQL
from libs.common.constants.league_constants import RIFT_WRAPPED_SYSTEM_PROMPT
from services.power_level_service import PowerLevelService
from api.power_levels.dtos import PowerLevel
from api.power_levels.metrics.dtos import PowerLevelMetrics
from api.helpers import get_http_service, get_rds, get_power_level_service, get_bedrock_runtime_client
import os, boto3, json, logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError

router = APIRouter(prefix='/power-levels/{puuid}', tags=['power-levels'])
log = logging.getLogger(__name__)

@router.get('')
def find_all(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), rds: RdsDataService = Depends(get_rds)):
    '''
    Gets all players match power level from AWS Aurora RDS
    '''
    return rds.query(GET_PLAYER_POWER_LEVELS_SQL, {"puuid": puuid, "skip": skip, "limit": limit})

@router.get('/by-match-id/{match_id}')
def find_one_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets the power level of the player with the match ID specified by PUUID
    '''
    row = rds.query_one(CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL, {"puuid": puuid, "match_id": match_id})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Power level with the match_id does not exists!")
    
    return rds.query_one(GET_PLAYER_MATCH_POWER_LEVEL_SQL, {"puuid": puuid, "match_id": match_id})
    
@router.get('/wrapped')
def get_player_power_level_wrapped(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], rds_service: RdsDataService = Depends(get_rds), bedrock_client: boto3.Session.client = Depends(get_bedrock_runtime_client)):
    '''
    Gets the "Spotify Wrapped" data from the power level of the player
    '''
    if not (KB_ID := os.getenv('KB_ID')) or not (MODEL_ARN := os.getenv("MODEL_ARN")):
        raise HTTPException(status_code=500, detail="KB_ID or MODEL_ARN not configured")
    
    # Get the aggregated player power level metrics
    
    # time window: last year → now (epoch seconds)
    now_dt = datetime.now(timezone.utc)
    # limit until Jan 1st of current year
    last_year_dt = now_dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    start_time = int(last_year_dt.timestamp())
    end_time = int(now_dt.timestamp())
    
    aggregated_player_metrics = rds_service.query_one(GET_AGGREGATED_YEARLY_METRICS_SQL, params={"puuid": puuid, "start_ts": start_time, "end_ts": end_time})
    
    print(aggregated_player_metrics)
    # create the prompt
    player_json = json.dumps(aggregated_player_metrics, separators=(",", ":"), ensure_ascii=False)
    prompt = RIFT_WRAPPED_SYSTEM_PROMPT.replace("<<<PASTE PLAYER JSON HERE>>>", player_json)
    
    try:
        response = bedrock_client.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": MODEL_ARN,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                            "overrideSearchType": "HYBRID",
                            "numberOfResults": 10
                        },
                        "metadataConfiguration": {
                            "filters": {
                                "andAll": [
                                    {"in": {"key": "type", "values": ["glossary","rubric","templates","style","example", "aggregation"]}},
                                    {"equals": {"key": "patch", "value": "14"}},
                                    {"equals": {"key": "lang", "value": "en"}}
                                ]
                            }
                        }
                    }
                }
            },
             generationConfiguration={
                "inferenceConfig": {"textInferenceConfig": {"temperature": 0.4, "maxTokens": 1000}},
                "responseStyle": {"styleType": "JSON"}
            }
        )
        
        body = response["output"]["text"]
        
        return json.loads(body) if body and body.strip().startswith("{") else body
    except ClientError as ce:
        log.exception('Bedrock runtime client error - %s', ce)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Error with Bedrock runtime client: {ce}')
    except Exception as e:
        log.exception('Error generating wrapped content for player - %s', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=f"Internal Server error - {e}")

@router.post('/by-match-id/{match_id}')
def upsert(createPowerLevelDto: PowerLevel, puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    """
    Creates (or updates if exist) a power level row in DB for the given PUUID with match ID

    Args:
        createPowerLevelDto (PowerLevel): _description_
        puuid (Annotated[str, Path, optional): _description_. Defaults to 'The Riot PUUID of the player to get')].
        match_id (Annotated[str, Path, optional): _description_. Defaults to 'The match ID of the match that player is in')].
        rds (RdsDataService, optional): _description_. Defaults to Depends(get_rds).

    Returns:
        _type_: _description_
    """
    
    return rds.exec(POWER_LEVEL_INSERT_SQL, {"puuid": puuid, "match_id": match_id, **createPowerLevelDto.model_dump()})

@router.post('/generate-by-metrics')
def generate_power_level_by_metrics(metrics: PowerLevelMetrics, power_level_service: PowerLevelService = Depends(get_power_level_service)) -> PowerLevelMetrics:
    """
    Generates the power level of a match based on their metrics

    Args:
        metrics (PowerLevelMetrics): _description_
        puuid (Annotated[str, Path, optional): _description_. Defaults to 'The Riot PUUID of the player to get')].
        match_id (Annotated[str, Path, optional): _description_. Defaults to 'The match ID of the match that player is in')].
        http_service (RiotRateLimitAPI, optional): _description_. Defaults to Depends(get_http_service).
        power_level_service (PowerLevelService, optional): _description_. Defaults to Depends(get_power_level_service).

    Returns:
        PowerLevelMetrics: _description_
    """
    power_levels = power_level_service.calculate_power_level(metrics)
    
    return power_levels

@router.post('/generate-by-match-id/{match_id}')
def generate_power_level_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], metrics: PowerLevelMetrics, http_service: RiotRateLimitAPI = Depends(get_http_service), power_level_service: PowerLevelService = Depends(get_power_level_service)) -> PowerLevelMetrics:
    """
    Generates the power level of a match based on their match ID


    Args:
        metrics (PowerLevelMetrics): _description_
        puuid (Annotated[str, Path, optional): _description_. Defaults to 'The Riot PUUID of the player to get')].
        match_id (Annotated[str, Path, optional): _description_. Defaults to 'The match ID of the match that player is in')].
        http_service (RiotRateLimitAPI, optional): _description_. Defaults to Depends(get_http_service).
        power_level_service (PowerLevelService, optional): _description_. Defaults to Depends(get_power_level_service).

    Returns:
        PowerLevelMetrics: _description_
    """
    match_details = http_service.call_endpoint_with_rate_limit('https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'.format(match_id=match_id))
    
    if player_idx := match_details['metadata']['participants'].index(puuid) == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player does not exist for given PUUID!")
    
    # Generate the match metrics from the match details
    metrics = power_level_service.extract_all_metrics(match_details, player_idx)
    
    # Generate the power levels from the metrics
    power_levels = power_level_service.calculate_power_level(metrics)
    
    return power_levels