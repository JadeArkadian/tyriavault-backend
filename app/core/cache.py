import hashlib
from typing import Any, Callable

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from starlette.requests import Request
from starlette.responses import Response

from app.core.utils import split_bearer_token


def cache_key_builder(func: Callable[..., Any], namespace: str = "default", *, request: Request = None,
                      response: Response = None, args: tuple = (), kwargs: dict = None) -> str:
    if kwargs is None:
        kwargs = {}

    try:
        auth = kwargs.get("authorization", "")
        if not auth and request:
            auth = request.headers.get("authorization", "")
        token = split_bearer_token(auth)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16] if token else "no_token"
        return f"{namespace}:{request.url.query}:{func.__name__}:{token_hash}"
    except RuntimeError | ValueError:
        # Fallback to a generic key if something goes wrong
        return f"{namespace}:{request.url.query}:{func.__name__}:unknown"


async def init_cache() -> None:
    FastAPICache.init(InMemoryBackend(), prefix="tyriavault")
