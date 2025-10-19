import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


@pytest.fixture(scope="session", autouse=True)
def init_cache_session():
    FastAPICache.init(InMemoryBackend(), prefix="tyriavault")


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    from app.main import api
    api.dependency_overrides = {}
    yield
    api.dependency_overrides = {}
