import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


@pytest.fixture(scope="session", autouse=True)
def init_cache_session():
    FastAPICache.init(InMemoryBackend(), prefix="tyriavault")


@pytest_asyncio.fixture(autouse=True)
async def clear_cache():
    """Clear cache before each test"""
    await FastAPICache.clear()
    yield
    await FastAPICache.clear()


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    from app.main import api
    api.dependency_overrides = {}
    yield
    api.dependency_overrides = {}


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_gw2_client():
    """Initialize GW2 client for tests"""
    from app.gw2.client import startup_gw2_client, shutdown_gw2_client
    await startup_gw2_client()
    yield
    await shutdown_gw2_client()
