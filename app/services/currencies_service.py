import asyncio
from typing import Any

from fastapi_cache.decorator import logger

from app.core.constants import Constants
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client


class CurrenciesService:

    def __init__(self, repository: CurrenciesRepository, gw2_client: GW2Client):
        self.repository = repository
        self.gw2_client = gw2_client

    async def get_all_currencies(self) -> list[dict]:
        """
        Get all currencies from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            currencies_data = await self._get_currencies_from_api()

            # Sync with db in background
            asyncio.create_task(self._sync_currencies_to_db(currencies_data))

            return currencies_data
        except Exception as e:
            logger.warning(f"Failed to fetch currencies from GW2 API: {e}. Falling back to database.")
            return await self._get_currencies_from_db()

    async def _get_currencies_from_api(self) -> list[dict]:
        """Fetch currencies from GW2 API in all supported languages and combine the data."""
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

    async def _get_currencies_from_db(self) -> list[dict]:
        """Fetch currencies from database as fallback."""
        try:
            currencies = await self.repository.get_all()

            if not currencies:
                logger.error("No currencies found in database for fallback")
                raise RuntimeError("No currencies available from API or database")

            # Convert ORM objects to dictionaries
            currencies_data = []
            for currency in currencies:
                currencies_data.append({
                    "id": currency.id,
                    "name_en": currency.name_en,
                    "name_es": currency.name_es,
                    "name_de": currency.name_de,
                    "name_fr": currency.name_fr,
                    "description_en": currency.description_en,
                    "description_es": currency.description_es,
                    "description_de": currency.description_de,
                    "description_fr": currency.description_fr,
                    "icon_url": currency.icon_url
                })

            logger.info(f"Retrieved {len(currencies_data)} currencies from database as fallback")
            return currencies_data
        except Exception as e:
            logger.error(f"Failed to retrieve currencies from database: {e}")
            raise

    async def _sync_currencies_to_db(self, currencies_data: list[dict]) -> None:
        """Sync currencies to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = CurrenciesRepository(session)
                await repository.upsert_batch(currencies_data)
            logger.info(f"Synced {len(currencies_data)} currencies to database")
        except Exception as e:
            logger.error(f"Error syncing currencies to database: {e}")
