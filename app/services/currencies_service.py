import asyncio
from typing import Any

from app.core.constants import Constants
from app.core.utils import handle_gw2_api_error
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.gw2.client import GW2Client


class CurrenciesService:

    def __init__(self, repository: CurrenciesRepository, gw2_client: GW2Client):
        self.repository = repository
        self.gw2_client = gw2_client

    async def get_all_currencies(self) -> list[dict]:
        currencies_data = await self._get_currencies_info_from_api()
        # TODO: Sync DB here
        return currencies_data

    async def _get_currencies_info_from_api(self) -> list[dict]:
        try:
            results = await asyncio.gather(
                *(self.gw2_client.get_currencies(lang=lang) for lang in Constants.LANGS)
            )

            combined_currencies: dict[int, dict[str, Any]] = {}

            for lang, currencies in zip(Constants.LANGS, results, strict=True):
                for currency in currencies:
                    currency_id = currency["id"]
                    if currency_id not in combined_currencies:
                        combined_currencies[currency_id] = {
                            "id": currency_id,
                            "icon_url": currency["icon"]
                        }
                    combined_currencies[currency_id][f"name_{lang}"] = currency["name"]
                    combined_currencies[currency_id][f"description_{lang}"] = currency["description"]
            return list(combined_currencies.values())
        except Exception as e:
            handle_gw2_api_error(e)
