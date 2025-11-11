import hashlib
from typing import Any, Callable

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import logger
from app.core.utils import split_bearer_token


def cache_key_builder(func: Callable[..., Any], namespace: str = "default", *, request: Request = None,
                      response: Response = None, args: tuple = (), kwargs: dict = None) -> str:
    if kwargs is None:
        kwargs = {}

    query_part = ""
    if request is not None:
        query_part = request.url.query

    try:
        auth = kwargs.get("authorization", "")
        if not auth and request is not None:
            auth = request.headers.get("authorization", "")
        token = split_bearer_token(auth)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16] if token else "no_token"
        return f"{namespace}:{query_part}:{func.__name__}:{token_hash}"
    except (RuntimeError, ValueError):
        # Fallback to a generic key if token extraction fails
        return f"{namespace}:{query_part}:{func.__name__}:unknown"


async def init_cache() -> None:
    """
    Initialize cache backend.

    Tries to connect to Redis if REDIS_URL is configured.
    Falls back to InMemory cache if Redis is not available or connection fails.
    """
    backend = None
    cache_type = "InMemory"

    # Try to use Redis if configured
    if settings.REDIS_URL:
        try:
            logger.info(f"Attempting to connect to Redis at {settings.REDIS_URL}")
            redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3
            )
            # Test connection
            await redis.ping()
            backend = RedisBackend(redis)
            cache_type = "Redis"
            logger.info("✅ Successfully connected to Redis cache")
        except Exception as e:
            logger.warning(f"⚠️ Failed to connect to Redis: {e}")
            logger.info("Falling back to InMemory cache")
            backend = InMemoryBackend()
    else:
        logger.info("REDIS_URL not configured, using InMemory cache")
        backend = InMemoryBackend()

    FastAPICache.init(backend, prefix="tyriavault")
    logger.info(f"Cache initialized with {cache_type} backend")
