import asyncio
from typing import Any

import httpx
import orjson

from app.core.config import settings
from app.core.logging import logger
from app.gw2.gw2_client import GW2Client, get_gw2_http_client


class GW2CrawlerClient(GW2Client):
    """
    Specialized GW2 Client for crawlers and background tasks.

    Differences from GW2Client:
    - NO circuit breaker protection (crawlers need to persist)
    - Higher timeout (30s vs 3s)
    - More retries (10 vs 2)
    - Aggressive backoff for persistent fetching
    - Designed for background tasks, not user-facing requests

    Use this for:
    - Items crawler
    - Data synchronization tasks
    - Background population of database
    - Scheduled tasks

    Do NOT use for:
    - API endpoints
    - User requests
    - Real-time data fetching
    """

    def __init__(
            self,
            api_key: str | None = None,
            max_retries: int | None = None,
            backoff_factor: float | None = None,
            timeout: int | None = None
    ):
        """
        :param api_key: Optional API key for authenticated requests
        :param max_retries: Max retries (default from settings: 10)
        :param backoff_factor: Backoff multiplier (default: 2.0)
        :param timeout: Timeout per request (default: 30s)
        """
        # Initialize parent but don't use its _get method
        self.api_key = api_key
        self.max_retries = max_retries if max_retries is not None else settings.GW2_CRAWLER_MAX_RETRIES
        self.backoff_factor = backoff_factor if backoff_factor is not None else settings.GW2_CRAWLER_BACKOFF_FACTOR
        self.timeout = timeout if timeout is not None else settings.GW2_CRAWLER_TIMEOUT_SECONDS
        self.client = get_gw2_http_client()

    async def _get(self, endpoint: str, params: dict | None = None, require_token: bool = False) -> Any | None:
        """
        Crawler-specific GET request WITHOUT circuit breaker.
        Retries persistently with exponential backoff.

        :param endpoint: API endpoint
        :param params: Query parameters
        :param require_token: Whether authentication is required
        :raises ValueError: If token is required and there is no API key
        :raises RuntimeError: If all retries are exceeded
        :return: Parsed response data
        """
        if require_token and not self.api_key:
            raise ValueError(f"This endpoint requires an API key to work: {endpoint}")

        retries = 0
        while True:
            try:
                # Direct call WITHOUT circuit breaker protection
                response = await asyncio.wait_for(
                    self.client.get(endpoint, params=params, headers=self._headers()),
                    timeout=self.timeout
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    header_val = response.headers.get("Retry-After")
                    try:
                        retry_after = int(header_val) if header_val is not None else None
                    except (TypeError, ValueError):
                        retry_after = None

                    wait_time = (retry_after
                                 if retry_after and retry_after > 0
                                 else self.backoff_factor * (2 ** retries))

                    logger.warning(f"[CRAWLER] Rate limit reached. Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    retries += 1
                    if retries > self.max_retries:
                        raise RuntimeError(f"Too many retries after rate limiting (max: {self.max_retries})")
                    continue

                # Retry on 5xx errors
                if 500 <= response.status_code < 600:
                    retries += 1
                    if retries > self.max_retries:
                        logger.error(f"[CRAWLER] Max retries exceeded on {response.status_code} error")
                        response.raise_for_status()
                    wait_time = self.backoff_factor * (2 ** (retries - 1))
                    logger.warning(
                        f"[CRAWLER] Server error {response.status_code}, retrying in {wait_time:.1f}s... ({retries}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return orjson.loads(response.content)

            except asyncio.TimeoutError:
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"[CRAWLER] Connection timeout after {self.max_retries} attempts")
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                logger.warning(
                    f"[CRAWLER] Timeout after {self.timeout}s, retrying in {wait_time:.1f}s... ({retries}/{self.max_retries})")
                await asyncio.sleep(wait_time)

            except httpx.RequestError as e:
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"[CRAWLER] Connection error after {self.max_retries} attempts: {e}")
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                logger.warning(
                    f"[CRAWLER] Network error: {e}. Retrying in {wait_time:.1f}s... ({retries}/{self.max_retries})")
                await asyncio.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                # 4xx errors (except 429 handled above) - don't retry
                logger.error(f"[CRAWLER] HTTP error {e.response.status_code} for {endpoint}: {e}")
                raise RuntimeError(f"HTTP {e.response.status_code}: {str(e)}")
