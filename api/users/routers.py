from fastapi import APIRouter, Path, Depends, Request, HTTPException, status
from libs.common.rds_service import RdsDataService
from libs.common.constants.users_queries import GET_USER_SQL, GET_ALL_USERS_SQL, INSERT_USER_SQL, CHECK_IF_USER_EXISTS_SQL, UPDATE_USER_SQL
from api.users.dtos import CreateUserDto, UpdateUserDto
from typing import Annotated

router = APIRouter(prefix='/users', tags=['users'])

def get_rds(request: Request) -> RdsDataService:
    return request.app.state.rds

@router.get('')
def find_all(skip: int = 0, limit: int = 10, rds: RdsDataService = Depends(get_rds)):
    '''
    Gets all users from Aurora RDS DB
    Parameters:
    skip - skips first [skip] rows, defaults to 0
    limit - limits the number of rows returned, defaults to 10
    '''
    return rds.query(GET_ALL_USERS_SQL, {"limit": limit, "skip": skip})

@router.get('/{puuid}')
def find_one_by_puuid(puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets a user by PUUID from Aurora RDS DB
    Parameters:
    puuid - The Riot PUUID of the player to get
    '''
    row = rds.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": puuid})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not exists!")
    
    return rds.query_one(GET_USER_SQL, {"puuid", puuid})

@router.post('/')
def create(createUserDto: CreateUserDto, rds: RdsDataService = Depends(get_rds)):
    '''
    Creates a user into Aurora RDS DB
    Body:
    createUserDto - The user object
    '''
    row = rds.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": createUserDto.puuid})
    if bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists!")
    
    return rds.exec(INSERT_USER_SQL, {"puuid": createUserDto.puuid, "game_name": createUserDto.game_name, "tag_line": createUserDto.tag_line})

@router.patch('/{puuid}')
def update(updateUserDto: UpdateUserDto, puuid: Annotated[str, Path(title='The Riot PUUID of the player to get')], rds: RdsDataService = Depends(get_rds)):
    '''
    Gets a user by PUUID from Aurora RDS DB
    Parameters:
    puuid - The Riot PUUID of the player to get
    '''
    row = rds.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": puuid})
    if not bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not exists!")
    
    return rds.exec(UPDATE_USER_SQL, {"puuid": puuid, "game_name": updateUserDto.game_name, "tag_line": updateUserDto.tag_line})