import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.cache import init_cache
from app.core.config import settings
from app.core.logging import logger
from app.crawlers import CrawlerScheduler, ItemsCrawler
from app.database.seeding.seeder import DatabaseSeeder
from app.database.session import async_session_maker
from app.gw2.client import startup_gw2_client, shutdown_gw2_client, GW2Client

# Install uvloop for better async performance (Unix-like systems only)
if sys.platform != 'win32':
    import uvloop

    logger.info("Using uvloop for improved performance...")
    uvloop.install()

log_filename = f"tyriavault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = os.path.join(os.path.dirname(__file__), log_filename)

# Global scheduler instance
crawler_scheduler = CrawlerScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Turning On...")
    await startup_gw2_client()

    # Initialize the TTL cache
    await init_cache()

    async with async_session_maker() as session:
        seeder = DatabaseSeeder(session)
        await seeder.seed_all()

    # Initialize and start crawlers
    logger.info("Initializing crawlers...")
    gw2_client = GW2Client(max_retries=5, backoff_factor=1.0)
    items_crawler = ItemsCrawler(gw2_client, async_session_maker)
    crawler_scheduler.register_crawler(
        name="items_crawler",
        crawler=items_crawler,
        interval_seconds=settings.ITEMS_CRAWLER_INTERVAL_SECONDS,
        fail_interval_seconds=150
    )

    # Start all crawlers (fire and forget)
    await crawler_scheduler.start_all()
    logger.info("All crawlers started")

    logger.info("Server is up and running!")
    yield
    # Shutdown
    logger.info("Turning Off...")
    await crawler_scheduler.stop_all()
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
