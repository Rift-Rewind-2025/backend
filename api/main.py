from fastapi import FastAPI, Request
from libs.common.rds_service import RdsDataService
from api.power_level.routers import router as power_level_router
from api.users.routers import router as users_router
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rds = RdsDataService.from_env()  # reads env here
    try:
        yield
    finally:
        # shutdown (nothing to close for Data API, but keep the hook)
        # If you had a DB pool: await app.state.pool.close()
        app.state.rds = None

app = FastAPI(title="Rift Rewind API", lifespan=lifespan)

@app.get('/')
def get():
    return {"message": "Hello World!"}

# include the routers
app.include_router(power_level_router)
app.include_router(users_router)