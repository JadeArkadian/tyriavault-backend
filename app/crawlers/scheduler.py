"""
Scheduler for running crawlers at regular intervals.
Supports multiple crawlers with independent schedules.
"""
import asyncio
from typing import Dict

from app.core.logging import logger
from app.crawlers.base_crawler import BaseCrawler


class CrawlerScheduler:
    """
    Manages scheduled execution of crawlers.
    Each crawler runs on its own interval defined in seconds.
    """

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._crawlers: Dict[str, tuple[BaseCrawler, int]] = {}

    def register_crawler(self, name: str, crawler: BaseCrawler, interval_seconds: int):
        self._crawlers[name] = (crawler, interval_seconds)
        logger.info(f"Registered crawler '{name}' with {interval_seconds}s interval")

    async def start_all(self):
        """Start all registered crawlers as background tasks."""
        for name, (crawler, interval) in self._crawlers.items():
            task = asyncio.create_task(self._run_crawler_loop(name, crawler, interval))
            self._tasks[name] = task
            logger.info(f"Started scheduler for crawler '{name}'")

    async def _run_crawler_loop(self, name: str, crawler: BaseCrawler, interval_seconds: int):
        """Run a crawler in an infinite loop with specified interval."""
        while True:
            try:
                logger.info(f"Executing crawler '{name}'...")
                await crawler.crawl()
                logger.info(f"Crawler '{name}' completed. Next run in {interval_seconds}s")
            except Exception as e:
                logger.error(f"Error in crawler '{name}': {e}", exc_info=True)
                logger.info(f"Crawler '{name}' will retry in {interval_seconds}s")

            await asyncio.sleep(interval_seconds)

    async def stop_all(self):
        """Cancel all running crawler tasks."""
        for name, task in self._tasks.items():
            task.cancel()
            logger.info(f"Stopped crawler '{name}'")

        # Wait for all tasks to finish cancellation
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
