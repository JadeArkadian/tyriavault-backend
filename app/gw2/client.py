import asyncio
from typing import Any

import httpx
import orjson

from app.core.logging import logger
from app.gw2.responses import GW2ApiAccount, GW2ApiColor, GW2ApiCurrency, GW2ApiTokenInfo, GW2ApiWalletEntry, GW2ApiWorld

BASE_URL = "https://api.guildwars2.com/v2"

_gw2_http_client: httpx.AsyncClient | None = None


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
    _gw2_http_client = httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)


async def shutdown_gw2_client():
    """To be called during application shutdown."""
    global _gw2_http_client
    if _gw2_http_client:
        await _gw2_http_client.aclose()
        _gw2_http_client = None


class GW2Client:
    def __init__(
            self,
            api_key: str | None = None,
            max_retries: int = 3,
            backoff_factor: float = 1.5,
    ):
        """
        :param api_key: Optional API key for authenticated requests.
        :param max_retries: Maximum number of retries for failed requests.
        :param backoff_factor: Multiplier for calculating wait time between retries.
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.client = get_gw2_http_client()

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    async def _get(self, endpoint: str, params: dict | None = None, require_token: bool = False) -> Any | None:
        if require_token and not self.api_key:
            raise ValueError(f"This endpoint requires an API key to work: {endpoint}")

        retries = 0
        while True:
            try:
                response = await self.client.get(endpoint, params=params, headers=self._headers())

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
                        raise RuntimeError("Too many retries after rate limiting.")
                    continue

                if 500 <= response.status_code < 600:
                    retries += 1
                    if retries > self.max_retries:
                        response.raise_for_status()
                    wait_time = self.backoff_factor * (2 ** (retries - 1))
                    logger.error(f"Error {response.status_code}, retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return orjson.loads(response.content)

            except httpx.RequestError as e:
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"Connection error after {self.max_retries} attempts.") from e
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                logger.warning(f"Network error: {e}. Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

    async def get_build(self) -> dict:
        """
        Get the current build id of the game.
        This is a public endpoint that doesn't require authentication.
        """
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

    async def get_item(self, item_id: int) -> dict:
        return await self._get(f"/items/{item_id}")
