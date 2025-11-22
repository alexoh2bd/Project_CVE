from fastapi import FastAPI
from app.api.routers import api_router

app = FastAPI(title="CVE Model Inference API")

app.include_router(api_router)
