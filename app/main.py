from fastapi import FastAPI

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import engine

# Setting up FastApi and our services
api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)
api.include_router(api_router, prefix="/api/v1")

print(settings.DATABASE_URL)

# creates tables if not present
from app.db.model import Base
Base.metadata.create_all(bind=engine)

