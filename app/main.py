import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.crawlers.worlds_crawler import update_worlds_incremental
from app.db.dependency import get_db
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

    # execute the worlds crawler once at startup
    await run_worlds_crawler_startup()

    # Schedule the worlds crawler to run daily at 5:00 AM
    scheduler = schedule_worlds_crawler_daily()

    yield
    # Shutdown
    print("Turn Off")
    await shutdown_gw2_client()
    scheduler.shutdown()


def run_worlds_crawler_startup():
    async def _run():
        async for db in get_db():
            await update_worlds_incremental(db)
            break

    return _run()


def schedule_worlds_crawler_daily():
    scheduler = AsyncIOScheduler()

    def schedule_crawler():
        async def run():
            async for db in get_db():
                await update_worlds_incremental(db)
                break

        asyncio.create_task(run())

    scheduler.add_job(schedule_crawler, 'cron', hour=22, minute=29)
    scheduler.start()
    return scheduler


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
