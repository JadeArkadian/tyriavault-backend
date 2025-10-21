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
