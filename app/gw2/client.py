import time

import httpx

BASE_URL = "https://api.guildwars2.com/v2"


class GW2Client:
    def __init__(
            self,
            timeout: float = 10.0,
            api_key: str | None = None,
            max_retries: int = 3,
            backoff_factor: float = 1.5,
    ):
        """
        :param timeout: Time in seconds to wait for a response before timing out.
        :param api_key: Optional API key for authenticated requests.
        :param max_retries: Maximum number of retries for failed requests.
        :param backoff_factor: Multiplier for calculating wait time between retries.
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.client = httpx.Client(base_url=BASE_URL, timeout=timeout)

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _get(self, endpoint: str, params: dict | None = None, require_token: bool = False):
        if require_token and not self.api_key:
            raise ValueError(f"This endpoint requires an API key to work: {endpoint}")

        retries = 0
        while True:
            try:
                response = self.client.get(endpoint, params=params, headers=self._headers())

                # if rate limited (code 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    wait_time = retry_after or self.backoff_factor * (2 ** retries)
                    print(f"Rate limit reached. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    retries += 1
                    if retries > self.max_retries:
                        raise RuntimeError("Too many retries after rate limiting.")
                    continue

                # If there's a server error (5xx), retry
                if 500 <= response.status_code < 600:
                    retries += 1
                    if retries > self.max_retries:
                        response.raise_for_status()
                    wait_time = self.backoff_factor * (2 ** (retries - 1))
                    print(f"Error {response.status_code}, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue

                #  If successful response, return JSON
                response.raise_for_status()
                return response.json()

            except httpx.RequestError as e:
                retries += 1
                if retries > self.max_retries:
                    raise RuntimeError(f"Conection error after {self.max_retries} attemps: {e}")
                wait_time = self.backoff_factor * (2 ** (retries - 1))
                print(f"Network error: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

        response = self.client.get(endpoint, params=params, headers=self._headers())
        response.raise_for_status()
        return response.json()

    # -------------------------
    # High-level API methods
    # -------------------------

    def token_info(self):
        return self._get("/tokeninfo", require_token=True)

    def get_account(self):
        return self._get("/account", require_token=True)

    def get_item(self, item_id: int):
        return self._get(f"/items/{item_id}")

    def get_exchange_rates(self):
        return self._get("/commerce/exchange/coins")
