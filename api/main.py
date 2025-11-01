from fastapi import FastAPI, Request
from libs.common.rds_service import RdsDataService
from api.power_level.routers import router as power_level_router
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
            log.info("RDS client initialized.")
            yield
        except Exception:
            log.exception("Failed to initialize RDS client")
        finally:
            # shutdown (nothing to close for Data API, but keep the hook)
            app.state.rds = None

app = FastAPI(title="Rift Rewind API", lifespan=lifespan)

@app.get('/')
def hello_world():
    return {"message": "Hello World!"}

# include the routers
app.include_router(power_level_router)
app.include_router(users_router)