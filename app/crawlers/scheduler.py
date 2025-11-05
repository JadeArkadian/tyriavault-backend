"""
Scheduler for running crawlers at regular intervals.
Supports multiple crawlers with independent schedules.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional

from app.core.logging import logger
from app.crawlers.base_crawler import BaseCrawler
from app.crawlers.status import CrawlerStatus, CrawlerState


class CrawlerScheduler:
    """
    Manages scheduled execution of crawlers.
    Each crawler runs on its own interval defined in seconds.
    """

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._crawlers: Dict[str, tuple[BaseCrawler, int, int]] = {}
        self._states: Dict[str, CrawlerState] = {}

    def register_crawler(self, name: str, crawler: BaseCrawler, interval_seconds: int, fail_interval_seconds: int = 300):
        self._crawlers[name] = (crawler, interval_seconds, fail_interval_seconds)
        self._states[name] = CrawlerState(name=name, status=CrawlerStatus.IDLE)
        logger.info(f"Registered crawler '{name}' with {interval_seconds}s interval")

    def get_crawler_state(self, name: str) -> Optional[CrawlerState]:
        """Get the current state of a specific crawler."""
        return self._states.get(name)

    def get_all_states(self) -> Dict[str, CrawlerState]:
        """Get the current state of all crawlers."""
        return self._states.copy()

    def is_crawler_running(self, name: str) -> bool:
        """Check if a crawler is currently running."""
        state = self._states.get(name)
        return state.status == CrawlerStatus.RUNNING if state else False

    def has_crawler_failed(self, name: str) -> bool:
        """Check if a crawler is in failed state."""
        state = self._states.get(name)
        return state.status == CrawlerStatus.FAILED if state else False

    async def start_all(self):
        """Start all registered crawlers as background tasks."""
        for name, (crawler, interval, fail_interval) in self._crawlers.items():
            task = asyncio.create_task(self._run_crawler_loop(name, crawler, interval, fail_interval))
            self._tasks[name] = task
            logger.info(f"Started scheduler for crawler '{name}'")

    async def stop_all(self):
        """Cancel all running crawler tasks."""
        for name, task in self._tasks.items():
            task.cancel()
            logger.info(f"Stopped crawler '{name}'")

        # Wait for all tasks to finish cancellation
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _run_crawler_loop(self, name: str, crawler: BaseCrawler, interval_seconds: int, fail_interval_seconds: int):
        """Run a crawler in an infinite loop with specified interval."""
        state = self._states[name]

        while True:
            try:
                # Update state to RUNNING
                state.status = CrawlerStatus.RUNNING
                state.last_run = datetime.now()
                state.total_runs += 1

                logger.info(f"Executing crawler '{name}'...")
                await crawler.crawl()

                # Update state to WAITING after successful run
                state.status = CrawlerStatus.WAITING

                logger.info(f"Crawler '{name}' completed. Next run in {interval_seconds}s")
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                logger.info(f"Cancellation received for crawler '{name}'. Stopping loop.")
                state.status = CrawlerStatus.IDLE
                raise

            except Exception as e:
                # Update state to FAILED
                state.status = CrawlerStatus.FAILED
                state.total_errors += 1

                logger.error(f"Error in crawler '{name}': {e}", exc_info=True)
                logger.info(f"Crawler '{name}' will retry in {fail_interval_seconds}s")
                await asyncio.sleep(fail_interval_seconds)
