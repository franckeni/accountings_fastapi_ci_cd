from fastapi import FastAPI
from mangum import Mangum

from shared.infrastructure.containers.fastapi_container import FastApiContainer

api: FastAPI = FastApiContainer().factory()
handler = Mangum(api) # For AWS lambda function
