import asyncio
from unittest.mock import AsyncMock

import pytest

from app.crawlers.scheduler import CrawlerScheduler


@pytest.mark.asyncio
async def test_register_crawler():
    """Test that a crawler can be registered correctly."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=60)

    # Verify that the crawler was registered
    assert "test_crawler" in scheduler._crawlers
    assert scheduler._crawlers["test_crawler"][0] == crawler_mock
    assert scheduler._crawlers["test_crawler"][1] == 60
    assert scheduler._crawlers["test_crawler"][2] == 300  # default fail_interval


@pytest.mark.asyncio
async def test_register_multiple_crawlers():
    """Test that multiple crawlers can be registered."""
    scheduler = CrawlerScheduler()
    crawler1 = AsyncMock()
    crawler2 = AsyncMock()

    scheduler.register_crawler("crawler1", crawler1, interval_seconds=30)
    scheduler.register_crawler("crawler2", crawler2, interval_seconds=60, fail_interval_seconds=120)

    # Verify that both crawlers were registered
    assert len(scheduler._crawlers) == 2
    assert "crawler1" in scheduler._crawlers
    assert "crawler2" in scheduler._crawlers
    assert scheduler._crawlers["crawler2"][2] == 120


@pytest.mark.asyncio
async def test_start_all_creates_tasks():
    """Test that start_all creates tasks for all registered crawlers."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=1)

    # Start the scheduler
    await scheduler.start_all()

    # Verify that a task was created
    assert "test_crawler" in scheduler._tasks
    assert isinstance(scheduler._tasks["test_crawler"], asyncio.Task)

    # Cleanup
    await scheduler.stop_all()


@pytest.mark.asyncio
async def test_crawler_executes_periodically():
    """Test that the crawler executes periodically according to the interval."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    # Register with a very short interval for testing (1 second)
    scheduler.register_crawler("test_crawler", crawler_mock, interval_seconds=1)

    # Start the scheduler
    await scheduler.start_all()

    # Wait a bit for it to execute several times
    await asyncio.sleep(3)

    # Stop the scheduler
    await scheduler.stop_all()

    # Verify that crawl was called at least 2-3 times
    assert crawler_mock.crawl.await_count >= 2


@pytest.mark.asyncio
async def test_crawler_handles_exceptions():
    """Test that the scheduler handles crawler exceptions and retries."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    # Make the crawler fail the first 2 times and then succeed
    call_count = 0

    async def failing_crawl():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Test error")

    crawler_mock.crawl = AsyncMock(side_effect=failing_crawl)

    # Register with short intervals for testing (1 second)
    scheduler.register_crawler("test_crawler", crawler_mock,
                               interval_seconds=1,
                               fail_interval_seconds=1)

    # Start the scheduler
    await scheduler.start_all()

    # Wait for it to execute several times
    await asyncio.sleep(4)

    # Stop the scheduler
    await scheduler.stop_all()

    # Verify that crawl was called multiple times despite the errors
    assert crawler_mock.crawl.await_count >= 3


@pytest.mark.asyncio
async def test_stop_all_cancels_tasks():
    """Test that stop_all cancels all scheduler tasks."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()
    crawler_mock.crawl = AsyncMock()

    scheduler.register_crawler("crawler1", crawler_mock, interval_seconds=10)
    scheduler.register_crawler("crawler2", crawler_mock, interval_seconds=10)

    # Start the scheduler
    await scheduler.start_all()

    # Verify that there are tasks
    assert len(scheduler._tasks) == 2

    # Stop the scheduler
    await scheduler.stop_all()

    # Verify that tasks were cleaned up
    assert len(scheduler._tasks) == 0


@pytest.mark.asyncio
async def test_multiple_crawlers_run_independently():
    """Test that multiple crawlers run independently."""
    scheduler = CrawlerScheduler()
    crawler1 = AsyncMock()
    crawler1.crawl = AsyncMock()
    crawler2 = AsyncMock()
    crawler2.crawl = AsyncMock()

    # Register with different intervals (1 and 3 seconds)
    scheduler.register_crawler("fast_crawler", crawler1, interval_seconds=1)
    scheduler.register_crawler("slow_crawler", crawler2, interval_seconds=3)

    # Start the scheduler
    await scheduler.start_all()

    # Wait
    await asyncio.sleep(5)

    # Stop the scheduler
    await scheduler.stop_all()

    # The fast crawler should have executed more times than the slow one
    assert crawler1.crawl.await_count > crawler2.crawl.await_count


@pytest.mark.asyncio
async def test_crawler_uses_fail_interval_on_error():
    """Test that the crawler uses fail_interval when there's an error."""
    scheduler = CrawlerScheduler()
    crawler_mock = AsyncMock()

    execution_times = []

    async def crawl_with_timing():
        import time
        execution_times.append(time.time())
        raise Exception("Test error")

    crawler_mock.crawl = AsyncMock(side_effect=crawl_with_timing)

    # Normal interval: 10s, failure interval: 1s
    scheduler.register_crawler("test_crawler", crawler_mock,
                               interval_seconds=10,
                               fail_interval_seconds=1)

    await scheduler.start_all()
    await asyncio.sleep(3.5)
    await scheduler.stop_all()

    # Should have executed at least 3 times with the short fail_interval
    assert len(execution_times) >= 3

    # Verify that the interval between executions is close to 1s
    if len(execution_times) >= 2:
        interval = execution_times[1] - execution_times[0]
        assert 0.5 < interval < 2.0  # Allow some variation


@pytest.mark.asyncio
async def test_empty_scheduler_start_stop():
    """Test that start_all and stop_all work with an empty scheduler."""
    scheduler = CrawlerScheduler()

    # Should not fail even if no crawlers are registered
    await scheduler.start_all()
    assert len(scheduler._tasks) == 0

    await scheduler.stop_all()
    assert len(scheduler._tasks) == 0
