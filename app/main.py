from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.db.model import Base
from app.db.session import engine
from app.gw2.client import startup_gw2_client, shutdown_gw2_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Turn On")
    print(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await startup_gw2_client()
    yield
    # Shutdown
    print("Turn Off")
    await shutdown_gw2_client()


# Setting up FastApi and our services
api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

origins = [settings.FRONTEND_URL]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

api.include_router(api_router, prefix="/api/v1")
