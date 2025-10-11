import os
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import logger
from app.crawlers.worlds_crawler import update_worlds_incremental
from app.db.data.seeding import seed_data
from app.db.dependency import get_db
from app.db.model import Base
from app.db.session import engine
from app.gw2.client import startup_gw2_client, shutdown_gw2_client

log_filename = f"tyriavault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(os.path.dirname(__file__), log_filename)


async def run_worlds_crawler_job():
    print("Running worlds crawler job")
    async for db in get_db():
        await update_worlds_incremental(db)
        break


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Turn On")
    logger.debug(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed almost invariable data
    async for db in get_db():
        await seed_data(db)
        break

    await startup_gw2_client()

    # execute the worlds crawler once at startup
    await run_worlds_crawler_startup()

    # Schedule the worlds crawler to run cada 2880 minutos (48h)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_worlds_crawler_job, 'interval', minutes=2880)
    scheduler.start()

    yield
    # Shutdown
    logger.info("Turn Off")
    await shutdown_gw2_client()
    scheduler.shutdown()


def run_worlds_crawler_startup():
    async def _run():
        async for db in get_db():
            await update_worlds_incremental(db)
            break

    return _run()


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
