from fastapi import APIRouter, Path, Query, Depends, HTTPException, status
from typing import Annotated
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from libs.common.constants.queries.power_level_metrics_queries import GET_PLAYER_MATCH_POWER_LEVEL_METRICS_SQL, GET_PLAYER_POWER_LEVEL_METRICS_SQL, CHECK_IF_MATCH_POWER_LEVEL_METRICS_EXISTS_SQL, POWER_LEVEL_METRICS_INSERT_SQL
from api.power_levels.metrics.dtos import PowerLevelMetrics
from api.helpers import get_rds, get_http_service, get_power_level_service
from services.power_level_service import PowerLevelService

router = APIRouter(prefix='/power-levels/{puuid}/metrics', tags=['power-levels-metrics'])

@router.get('')
def find_all(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), rds: RdsDataService = Depends(get_rds)):
    """
    Gets player's all match power level metrics
    """
    return rds.query(GET_PLAYER_POWER_LEVEL_METRICS_SQL, {"puuid": puuid, "skip": skip, "limit": limit})

@router.get('/by-match-id/{match_id}')
def find_one_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets the power level of the player with the match ID specified by PUUID
    '''
    row = rds.query_one(CHECK_IF_MATCH_POWER_LEVEL_METRICS_EXISTS_SQL, {"puuid": puuid, "match_id": match_id})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Power level with the match_id does not exists!")
    
    return rds.query_one(GET_PLAYER_MATCH_POWER_LEVEL_METRICS_SQL, {"puuid": puuid, "match_id": match_id})
    
@router.post('/by-match-id/{match_id}')
def upsert(createPowerLevelMetricsDto: PowerLevelMetrics, puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    """
    Creates (or updates if exist) a new metrics row for the player given their PUUID

    Args:
        createPowerLevelMetricsDto (PowerLevelMetrics): _description_
        puuid (Annotated[str, Path, optional): _description_. Defaults to 'The Riot PUUID of the player to get')].
        match_id (Annotated[str, Path, optional): _description_. Defaults to 'The match ID of the match that player is in')].
        rds (RdsDataService, optional): _description_. Defaults to Depends(get_rds).

    Returns:
        _type_: _description_
    """
    
    return rds.exec(POWER_LEVEL_METRICS_INSERT_SQL, {"puuid": puuid, "match_id": match_id, **createPowerLevelMetricsDto.model_dump()})

@router.post('/generate-by-match-id/{match_id}')
def generate_metrics_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], http_service: RiotRateLimitAPI = Depends(get_http_service), power_level_service: PowerLevelService = Depends(get_power_level_service)) -> PowerLevelMetrics:
    """
    Generates the metrics of a match based on their given PUUID

    Args:
        puuid (Annotated[str, Path, optional): _description_. Defaults to 'The Riot PUUID of the player to get')].
        match_id (Annotated[str, Path, optional): _description_. Defaults to 'The match ID of the match that player is in')].
        http_service (RiotRateLimitAPI, optional): _description_. Defaults to Depends(get_http_service).
        power_level_service (PowerLevelService, optional): _description_. Defaults to Depends(get_power_level_service).

    Raises:
        HTTPException: _description_

    Returns:
        PowerLevelMetrics: _description_
    """
    # Get the match details from Riot Match-V5 API
    match_details = http_service.call_endpoint_with_rate_limit('https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'.format(match_id=match_id))
    
    if player_idx := match_details['metadata']['participants'].index(puuid) == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player does not exist for given PUUID!")
    
    # Generate the match metrics from the match details
    metrics = power_level_service.extract_all_metrics(match_details, player_idx)
    
    return metrics