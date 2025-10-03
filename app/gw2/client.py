import httpx

BASE_URL = "https://api.guildwars2.com/v2"

class GW2Client:
    def __init__(self, timeout: float = 10.0, api_key: str | None = None):
        self.api_key = api_key
        self.client = httpx.Client(base_url=BASE_URL, timeout=timeout)

    def _headers(self):
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _get(self, endpoint: str, params: dict | None = None):
        response = self.client.get(endpoint, params=params, headers=self._headers())
        response.raise_for_status()
        return response.json()

    # Ejemplos de métodos de alto nivel
    def get_account(self):
        return self._get("/account")

    def get_item(self, item_id: int):
        return self._get(f"/items/{item_id}")

    def get_exchange_rates(self):
        return self._get("/commerce/exchange/coins")