"""
Manual test script for the crawler scheduler.
This script can be used to test the scheduler independently of the main application.
"""
import asyncio

from app.core.logging import logger
from app.crawlers import CrawlerScheduler, ItemsCrawler
from app.database.session import async_session_maker
from app.gw2.client import startup_gw2_client, shutdown_gw2_client, GW2Client


async def test_scheduler():
    """Test the crawler scheduler with a short interval."""
    logger.info("Testing crawler scheduler...")

    # Initialize GW2 client
    await startup_gw2_client()

    # Create scheduler
    gw2_client = GW2Client()
    scheduler = CrawlerScheduler()

    # Register items crawler with a shorter interval for testing (5 minutes)
    test_interval = 5 * 60  # 5 minutes instead of 24 hours
    items_crawler = ItemsCrawler(gw2_client, async_session_maker)
    scheduler.register_crawler(
        name="items_crawler_test",
        crawler=items_crawler,
        interval_seconds=test_interval
    )

    # Start scheduler
    await scheduler.start_all()

    # Let it run for a while (e.g., 15 minutes to see multiple executions)
    logger.info(f"Scheduler running. Will test for 15 minutes...")
    await asyncio.sleep(15 * 60)

    # Stop scheduler
    logger.info("Stopping scheduler...")
    await scheduler.stop_all()

    # Cleanup
    await shutdown_gw2_client()
    logger.info("Test completed")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
