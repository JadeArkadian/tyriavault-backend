import asyncio

import httpx

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

    async def _get(self, endpoint: str, params: dict | None = None, require_token: bool = False):
        if require_token and not self.api_key:
            raise ValueError(f"This endpoint requires an API key to work: {endpoint}")

        retries = 0
        while True:
            try:
                response = await self.client.get(endpoint, params=params, headers=self._headers())

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = retry_after or self.backoff_factor * (2 ** retries)
                    print(f"Rate limit reached. Retrying in {wait_time:.1f}s...")
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
                    print(f"Error {response.status_code}, retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.RequestError as e:
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"Conection error after {self.max_retries} attemps: {e}")
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                print(f"Network error: {e}. Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        response = await self.client.get(endpoint, params=params, headers=self._headers())
        response.raise_for_status()
        return response.json()

    async def token_info(self):
        return await self._get("/tokeninfo", require_token=True)

    async def get_account(self):
        return await self._get("/account", require_token=True)

    async def get_worlds(self, lang: str = "en"):
        return await self._get(f"/worlds?lang={lang}&ids=all", require_token=False)

    async def get_item(self, item_id: int):
        return await self._get(f"/items/{item_id}")

    async def get_exchange_rates(self):
        return await self._get("/commerce/exchange/coins")
