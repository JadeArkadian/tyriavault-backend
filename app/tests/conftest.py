import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


@pytest.fixture(scope="session", autouse=True)
def init_cache_session():
    """Inicializa FastAPICache una sola vez para toda la sesión de tests."""
    # Inicializamos directamente; si se llama dos veces FastAPICache simplemente sobrescribe backend y prefix.
    FastAPICache.init(InMemoryBackend(), prefix="tyriavault")
