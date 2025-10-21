import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.cache import init_cache
from app.core.config import settings
from app.core.logging import logger
from app.gw2.client import startup_gw2_client, shutdown_gw2_client

log_filename = f"tyriavault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(os.path.dirname(__file__), log_filename)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Turning On...")
    logger.debug(settings.DATABASE_URL)
    await startup_gw2_client()

    # Initialize the TTL cache
    await init_cache()

    logger.info("Server is up and running!")
    yield
    # Shutdown
    logger.info("Turning Off...")
    await shutdown_gw2_client()


# Setting up FastApi and our services
api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    redirect_slashes=False
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
