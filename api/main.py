from fastapi import FastAPI, Request
from libs.common.rds_service import RdsDataService
from libs.common.riot_rate_limit_api import RiotRateLimitAPI
from services.power_level_service import PowerLevelService
from api.power_levels.metrics.routers import router as power_level_metrics_router
from api.power_levels.routers import router as power_level_router
from api.users.routers import router as users_router
from contextlib import asynccontextmanager
import logging, os

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    required = ["DB_ARN", "SECRET_ARN", "DB_NAME"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        log.error("Missing required env vars: %s", missing)
    else:
        try:
            app.state.rds = RdsDataService.from_env()  # reads env here
            app.state.http_service = RiotRateLimitAPI() # reads RIOT_API_KEY env here
            app.state.power_level_service = PowerLevelService()
            log.info("RDS client, Riot HTTP client, and Power Level service initialized.")
            yield
        except Exception as e:
            log.exception(f"Failed to initialize RDS client, Riot HTTP client, and Power Level service - {e}")
        finally:
            # shutdown (nothing to close for Data API and Riot HTTP client, but keep the hook)
            app.state.rds = None
            app.state.http_service = None
            app.state.power_level_service = None

app = FastAPI(title="Rift Rewind API", lifespan=lifespan)

@app.get('/')
def hello_world():
    return {"message": "Hello World!"}

# include the routers
# include metrics routers first to define the static routers that are nested under power_level_router
app.include_router(power_level_metrics_router)

app.include_router(power_level_router)

app.include_router(users_router)