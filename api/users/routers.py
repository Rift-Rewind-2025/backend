from fastapi import APIRouter, Path, Depends, Request, HTTPException, status
from libs.common.rds_service import RdsDataService
from libs.common.constants.queries.users_queries import GET_USER_SQL, GET_ALL_USERS_SQL, INSERT_USER_SQL, CHECK_IF_USER_EXISTS_SQL, UPDATE_USER_SQL
from api.users.dtos import CreateUserDto, UpdateUserDto
from typing import Annotated
from api.helpers import get_rds, get_lambda_client, get_user_created_fn_name
import boto3, json, logging
from botocore.exceptions import ClientError

router = APIRouter(prefix='/users', tags=['users'])
log = logging.getLogger(__name__)


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

@router.post('')
def create(createUserDto: CreateUserDto, rds: RdsDataService = Depends(get_rds), lambda_client: boto3.Session.client = Depends(get_lambda_client), user_created_fn: str = Depends(get_user_created_fn_name)):
    '''
    Creates a user into Aurora RDS DB
    Body:
    createUserDto - The user object
    '''
    row = rds.query_one(CHECK_IF_USER_EXISTS_SQL, {"puuid": createUserDto.puuid})
    if bool(row['exists']):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists!")
    
    user = rds.exec(INSERT_USER_SQL, {"puuid": createUserDto.puuid, "game_name": createUserDto.game_name, "tag_line": createUserDto.tag_line})
    
    try:
        lambda_client.invoke( # invokes the get player match lambda function when user is created
            FunctionName=user_created_fn,
            InvocationType="Event",        # async
            Payload=json.dumps({"puuid": createUserDto.puuid}).encode("utf-8"),
        )
    except ClientError:
        log.exception("Failed to invoke %s", user_created_fn)
    
    return user

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