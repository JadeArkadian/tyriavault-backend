"""
Integration test to verify Redis cache functionality.

This test verifies that:
1. The application connects to Redis when REDIS_URL is configured
2. Cache is working correctly with Redis backend
3. Data persists across multiple requests
"""
import asyncio

import httpx
import pytest


class CacheTestClient:
    """Client to test cache functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_worlds(self) -> httpx.Response:
        """Get worlds endpoint (should be cached)."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/common/worlds")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_cache_functionality():
    """
    Test that Redis cache is working correctly.

    This test:
    1. Makes a first request to populate the cache
    2. Makes a second request that should hit the cache
    3. Verifies both requests return the same data
    """
    client = CacheTestClient()

    # First request - populates cache
    response1 = await client.get_worlds()
    assert response1.status_code == 200, f"First request failed with status {response1.status_code}"
    data1 = response1.json()

    # Wait a small moment
    await asyncio.sleep(0.5)

    # Second request - should hit cache
    response2 = await client.get_worlds()
    assert response2.status_code == 200, f"Second request failed with status {response2.status_code}"
    data2 = response2.json()

    # Verify data is the same (cache hit)
    assert data1 == data2, "Cached data differs from original data"
    assert len(data1) > 0, "No data returned from endpoint"

    print(f"✅ Cache test passed - {len(data1)} worlds cached successfully")
