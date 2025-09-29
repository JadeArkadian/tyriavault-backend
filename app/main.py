from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import api_router

api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

# Include the API router with a versioned prefix
api.include_router(api_router, prefix="/api/v1")