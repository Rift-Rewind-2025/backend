from fastapi import APIRouter, Path, Depends, HTTPException, status
from typing import Annotated
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from libs.common.constants.queries.power_level_queries import GET_PLAYER_MATCH_POWER_LEVEL_SQL, GET_PLAYER_POWER_LEVELS_SQL, CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL, POWER_LEVEL_INSERT_SQL
from services.power_level_service import PowerLevelService
from api.power_levels.dtos import PowerLevel
from api.power_levels.metrics.dtos import PowerLevelMetrics
from api.helpers import get_http_service, get_rds, get_power_level_service

router = APIRouter(prefix='/power-levels/{puuid}', tags=['power-level'])

@router.get('')
def find_all(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], skip: int = 0, limit: int = 10, rds: RdsDataService = Depends(get_rds)):
    '''
    Gets all players match power level from AWS Aurora RDS
    '''
    return rds.query(GET_PLAYER_POWER_LEVELS_SQL, {"puuid": puuid, "skip": skip, "limit": limit})

@router.get('/{match_id}')
def find_one_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets the power level of the player with the match ID specified by PUUID
    '''
    row = rds.query_one(CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL, {"puuid": puuid})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Power level with the match_id does not exists!")
    
    return rds.query_one(GET_PLAYER_MATCH_POWER_LEVEL_SQL, {"puuid": puuid, "match_id": match_id})
    
@router.get('/wrapped')
def get_player_power_level_wrapped(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')]):
    '''
    Gets the "Spotify Wrapped" data from the power level of the player
    '''
    return {'ok': True}

@router.post('/{match_id}')
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
    
    return rds.exec(POWER_LEVEL_INSERT_SQL, {"puuid": puuid, "match_id": match_id, **createPowerLevelDto.model_dump().items()})

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