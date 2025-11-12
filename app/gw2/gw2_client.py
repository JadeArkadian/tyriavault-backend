import asyncio
from typing import Any

import httpx
import orjson
from circuitbreaker import circuit, CircuitBreakerError

from app.core.config import settings
from app.core.logging import logger
from app.gw2.responses import GW2ApiAccount, GW2ApiColor, GW2ApiCurrency, GW2ApiTokenInfo, GW2ApiWalletEntry, GW2ApiWorld, GW2ApiItem

_gw2_http_client: httpx.AsyncClient | None = None


class GW2ApiError(Exception):
    """Specific exception for GW2 API failures"""
    pass


def get_gw2_http_client() -> httpx.AsyncClient:
    """
    Returns the shared httpx.AsyncClient instance.
    Raises a RuntimeError if the client is not initialized.
    """
    if _gw2_http_client is None:
        raise RuntimeError("GW2 HTTP client is not initialized.")
    return _gw2_http_client


async def startup_gw2_client():
    """To be called during application startup."""
    global _gw2_http_client
    _gw2_http_client = httpx.AsyncClient(
        base_url=settings.GW2_API_BASE_URL,
        timeout=httpx.Timeout(settings.GW2_API_TIMEOUT_SECONDS)
    )


async def shutdown_gw2_client():
    """To be called during application shutdown."""
    global _gw2_http_client
    if _gw2_http_client:
        await _gw2_http_client.aclose()
        _gw2_http_client = None


@circuit(
    failure_threshold=settings.GW2_API_CIRCUIT_FAILURE_THRESHOLD,
    recovery_timeout=settings.GW2_API_CIRCUIT_RECOVERY_TIMEOUT,
    expected_exception=GW2ApiError,
    name="gw2_api_circuit"
)
async def _protected_api_call(
        client: httpx.AsyncClient,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None
) -> httpx.Response:
    """
    Internal function protected by the circuit breaker.
    All API calls go through here.

    :param client: Shared HTTP client
    :param endpoint: Endpoint to call
    :param params: Optional query parameters
    :param headers: Optional headers (for authentication)
    :raises GW2ApiError: If there is a connection error, timeout or server error
    :return: httpx Response
    """
    try:
        response = await asyncio.wait_for(
            client.get(endpoint, params=params, headers=headers or {}),
            timeout=settings.GW2_API_TIMEOUT_SECONDS
        )

        # 5xx errors open the circuit breaker
        if 500 <= response.status_code < 600:
            logger.warning(f"GW2 API server error {response.status_code}: {endpoint}")
            raise GW2ApiError(f"API server error {response.status_code}")

        return response

    except asyncio.TimeoutError:
        logger.warning(f"GW2 API timeout after {settings.GW2_API_TIMEOUT_SECONDS}s: {endpoint}")
        raise GW2ApiError(f"API timeout for {endpoint}")
    except httpx.RequestError as e:
        logger.warning(f"GW2 API connection error: {e}")
        raise GW2ApiError(f"Connection error: {str(e)}")


class GW2Client:
    """
    GW2 API Client with Circuit Breaker protection.

    Designed for user-facing API endpoints that need fast responses.
    Uses circuit breaker to fail fast when API is down and fallback to database.

    Features:
    - Circuit breaker protection (fails fast after 3 consecutive errors)
    - Short timeout (3s)
    - Limited retries (2)
    - Quick fallback to database

    Use this for:
    - API endpoints (worlds, currencies, dyes, etc.)
    - User requests that need fast responses
    - Real-time data fetching
    """

    def __init__(
            self,
            api_key: str | None = None,
            max_retries: int | None = None,
            backoff_factor: float = 1.5,
    ):
        """
        :param api_key: Optional API key for authenticated requests.
        :param max_retries: Maximum number of retries for failed requests. Uses settings if not provided.
        :param backoff_factor: Multiplier for calculating wait time between retries.
        """
        self.api_key = api_key
        self.max_retries = max_retries if max_retries is not None else settings.GW2_API_MAX_RETRIES
        self.backoff_factor = backoff_factor
        self.client = get_gw2_http_client()

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    async def _get(self, endpoint: str, params: dict | None = None, require_token: bool = False) -> Any | None:
        """
        Makes a GET request to the GW2 API.
        Uses circuit breaker to fail fast when API is down.
        Handles rate limiting (429) and retries intelligently.

        :param endpoint: API endpoint
        :param params: Query parameters
        :param require_token: Whether authentication is required
        :raises GW2ApiError: If the circuit breaker is open or there is a fatal error
        :raises ValueError: If token is required and there is no API key
        :return: Parsed response data
        """
        if require_token and not self.api_key:
            raise ValueError(f"This endpoint requires an API key to work: {endpoint}")

        retries = 0
        while True:
            try:
                # This call is protected by the circuit breaker
                # If it's open, it throws CircuitBreakerError immediately
                response = await _protected_api_call(
                    self.client,
                    endpoint,
                    params=params,
                    headers=self._headers()
                )

                # Special handling of rate limiting (429)
                if response.status_code == 429:
                    header_val = response.headers.get("Retry-After")
                    try:
                        retry_after = int(header_val) if header_val is not None else None
                    except (TypeError, ValueError):
                        retry_after = None

                    wait_time = (retry_after
                                 if retry_after and retry_after > 0
                                 else self.backoff_factor * (2 ** retries))

                    logger.warning(f"Rate limit reached. Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    retries += 1
                    if retries > self.max_retries:
                        raise GW2ApiError("Too many retries after rate limiting.")
                    continue

                # Validate successful response
                response.raise_for_status()
                return orjson.loads(response.content)

            except CircuitBreakerError as e:
                # The circuit breaker is open - the API has failed many times
                logger.info(f"Circuit breaker is OPEN: {e}")
                raise GW2ApiError(f"Circuit breaker open: API is unavailable")
            except GW2ApiError:
                # API error (timeout, server error, etc.)
                # Propagate so services can fallback to DB
                raise
            except httpx.HTTPStatusError as e:
                # 4xx errors (except 429 which is already handled above)
                logger.error(f"HTTP error {e.response.status_code} for {endpoint}: {e}")
                raise GW2ApiError(f"HTTP {e.response.status_code}: {str(e)}")

    async def get_build(self) -> dict:
        """Get the current build id of the game."""
        return await self._get("/build", require_token=False)

    async def token_info(self) -> GW2ApiTokenInfo:
        """Get information about the current API token."""
        data = await self._get("/tokeninfo", require_token=True)
        return GW2ApiTokenInfo(**data)

    async def get_account(self) -> GW2ApiAccount:
        """Get account information."""
        data = await self._get("/account", require_token=True)
        return GW2ApiAccount(**data)

    async def get_worlds(self, lang: str = "en") -> list[GW2ApiWorld]:
        """Get all worlds with their names and population."""
        data = await self._get(f"/worlds?lang={lang}&ids=all", require_token=False)
        return [GW2ApiWorld(**world) for world in data]

    async def get_currencies(self, lang: str = "en") -> list[GW2ApiCurrency]:
        """Get all currencies with their names, descriptions, and icons."""
        data = await self._get(f"/currencies?lang={lang}&ids=all", require_token=False)
        return [GW2ApiCurrency(**currency) for currency in data]

    async def get_colors(self, lang: str = "en") -> list[GW2ApiColor]:
        """Get all colors/dyes with their names, material info, and categories."""
        data = await self._get(f"/colors?lang={lang}&ids=all", require_token=False)
        return [GW2ApiColor(**color) for color in data]

    async def get_wallet(self) -> list[GW2ApiWalletEntry]:
        """Get account wallet with all currencies and their amounts."""
        data = await self._get("/account/wallet", require_token=True)
        return [GW2ApiWalletEntry(**entry) for entry in data]

    async def get_all_item_ids(self) -> list[int]:
        """Get all item IDs available in the game."""
        return await self._get("/items", require_token=False)

    async def get_item_details(self, item_ids: list[int], lang: str = "en") -> list[GW2ApiItem]:
        """Get item details for given item IDs.
           Please note that the GW2 API limits the number of IDs per request.
        """
        item_ids_str = ",".join(map(str, item_ids))
        data = await self._get(f"/items?lang={lang}&ids={item_ids_str}")
        return [GW2ApiItem(**item) for item in data]
