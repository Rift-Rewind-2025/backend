from mangum import Mangum
from api.main import app

# ASGI app for AWS Lambda
handler = Mangum(app)