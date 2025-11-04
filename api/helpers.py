from fastapi import Request
from functools import lru_cache
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from services.power_level_service import PowerLevelService
import boto3, os
from botocore.config import Config

def get_rds(request: Request) -> RdsDataService:
    return request.app.state.rds

def get_http_service(request: Request) -> RiotRateLimitAPI:
    return request.app.state.http_service

def get_power_level_service(request: Request) -> PowerLevelService:
    return request.app.state.power_level_service

@lru_cache(maxsize=1)
def get_lambda_client() -> boto3.Session.client:
    """
    Lazily creates and memoizes the Lambda client.
    Not created unless POST /users calls this function.
    """
    cfg = Config(
        region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"), 
        retries={"max_attempts": 4, "mode": "standard"},
        read_timeout=20,
        connect_timeout=5,
                 )
    
    return boto3.client("lambda", config=cfg)

def get_user_created_fn_name(request: Request) -> str:
    return request.app.state.user_created_fn

@lru_cache(maxsize=1)
def get_bedrock_runtime_client() -> boto3.Session.client:
    """
    Lazily creates and memoizes the Bedrock Agent Runtime client.
    Not created unless GET /power-levels/{puuid}/wrapped calls this function.
    """
    cfg = Config(
        region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"), 
        retries={"max_attempts": 4, "mode": "standard"},
        read_timeout=20,
        connect_timeout=5,
                 )
    
    return boto3.client("bedrock-agent-runtime", config=cfg)