from fastapi import FastAPI, Request
from libs.common.rds_service import RdsDataService
from api.power_level.routers import router as power_level_router

app = FastAPI(title="Rift Rewind API")

@app.on_event("startup")
def _init_clients():
    app.state.rds = RdsDataService.from_env()  # reads env here

@app.get('/')
def get():
    return {"message": "Hello World!"}

# include the routers
app.include_router(power_level_router)