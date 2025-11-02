from fastapi import Request
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from services.power_level_service import PowerLevelService
import boto3

def get_rds(request: Request) -> RdsDataService:
    return request.app.state.rds

def get_http_service(request: Request) -> RiotRateLimitAPI:
    return request.app.state.http_service

def get_power_level_service(request: Request) -> PowerLevelService:
    return request.app.state.power_level_service

def get_lambda_client(request: Request) -> boto3.Session.client:
    return request.app.state.lambda_client

def get_user_created_fn_name(request: Request) -> str:
    return request.app.state.user_created_fn