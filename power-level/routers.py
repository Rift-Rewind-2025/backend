from fastapi import APIRouter, Path
from typing import Annotated
from power_level_service import PowerLevelService

router = APIRouter(prefix='/power-level', tags=['power-level'])

@router.get('/')
def get_player_power_levels():
    '''
    Gets all players power level from AWS DynamoDB
    '''

@router.get('/{puuid}')
def get_player_power_level_by_puuid(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')]):
    '''
    Gets the power level of the player specified by PUUID
    '''
    
@router.get('/{puuid}/wrapped')
def get_player_power_level_wrapped(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')]):
    '''
    Gets the "Spotify Wrapped" data from the power level of the player
    '''