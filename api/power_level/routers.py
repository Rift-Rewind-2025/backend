from fastapi import APIRouter, Path, Depends, Request, HTTPException, status
from typing import Annotated
from libs.common.rds_service import RdsDataService
from libs.common.constants.power_level_queries import GET_PLAYER_MATCH_POWER_LEVEL_SQL, GET_PLAYER_POWER_LEVELS_SQL, CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL
from services.power_level_service import PowerLevelService

router = APIRouter(prefix='/power-level/{puuid}', tags=['power-level'])

def get_rds(request: Request) -> RdsDataService:
    return request.app.state.rds

@router.get('/')
def find_all(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], skip: int = 0, limit: int = 10, rds: RdsDataService = Depends(get_rds)):
    '''
    Gets all players match power level from AWS Aurora RDS
    '''
    return rds.query(GET_PLAYER_POWER_LEVELS_SQL, {"puuid": puuid})

@router.get('/{match_id}')
def find_one_by_match_id(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], match_id: Annotated[str, Path(title='The match ID of the match that player is in')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets the power level of the player with the match ID specified by PUUID
    '''
    row = rds.query_one(CHECK_IF_MATCH_POWER_LEVEL_EXISTS_SQL, {"puuid": puuid})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Power level with the match_id does not exists!")
    
    return rds.query_one(GET_PLAYER_MATCH_POWER_LEVEL_SQL, {"puuid": puuid, "match_id": match_id})
    
@router.get('/wrapped')
def get_player_power_level_wrapped(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')]):
    '''
    Gets the "Spotify Wrapped" data from the power level of the player
    '''
    return {'ok': True}