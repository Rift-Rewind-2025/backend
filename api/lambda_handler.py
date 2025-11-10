from mangum import Mangum
from fastapi import Request
from fastapi.responses import JSONResponse
from api.main import app
import logging, uuid, json

log = logging.getLogger()
log.setLevel(logging.INFO)

# Log every request path (helps confirm routing)
@app.middleware('http')
async def _log_req(request: Request, call_next):
    log.info("REQ path=%s query=%s", request.url.path, request.url.query)
    return await call_next(request)

# Catch any uncaught expcetion and log full traceback
@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    err_id = str(uuid.uuid4())
    log.exception("UNHANDLED err_id=%s path=%s method=%s", err_id, request.url.path, request.method)
    
    return JSONResponse(status_code=500, content={"error": "internal_error", "id": err_id})

# ASGI app for AWS Lambda
_handler = Mangum(app)

def handler(event, context):
    try:
        log.info("EVENT %s", json.dumps(event)[:2000])
    except Exception:
        pass
    return _handler(event, context)