import asyncio

from app.core.constants import Constants
from app.core.logging import logger
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client
from app.services.models import CurrencyData


class CurrenciesService:
    """
    Service to manage currencies data from GW2 API and database.
    Currencies can change on some patches, or even appear for an event, so we try API first.

    Data fetch strategy: 1 - Try to get data from GW2 API
                         2 - If successful, return data and sync with DB in background
                         3 - If API fails, fallback to DB
                         4 - If both fail, raise error
    """

    def __init__(self, repository: CurrenciesRepository, gw2_client: GW2Client):
        self.repository = repository
        self.gw2_client = gw2_client
        self._background_tasks: set[asyncio.Task] = set()

    async def get_all_currencies(self) -> list[CurrencyData]:
        """
        Get all currencies from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            currencies_data = await self._get_currencies_from_api()

            # Sync with db in background
            task = asyncio.create_task(self._sync_currencies_to_db(currencies_data))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return currencies_data
        except Exception as e:
            logger.warning(f"Failed to fetch currencies from GW2 API: {e}. Falling back to database.")
            return await self._get_currencies_from_db()

    async def _get_currencies_from_api(self) -> list[CurrencyData]:
        """Fetch currencies from GW2 API in all supported languages and combine the data."""
        results = await asyncio.gather(
            *(self.gw2_client.get_currencies(lang=lang) for lang in Constants.LANGS)
        )

        combined_currencies: dict[int, dict[str, str | int | None]] = {}

        for lang, currencies in zip(Constants.LANGS, results, strict=True):
            for currency in currencies:
                currency_id = currency.id
                if currency_id not in combined_currencies:
                    combined_currencies[currency_id] = {
                        "id": currency_id,
                        "icon_url": currency.icon
                    }
                combined_currencies[currency_id][f"name_{lang}"] = currency.name
                combined_currencies[currency_id][f"description_{lang}"] = currency.description

        # Convert to CurrencyData objects
        return [CurrencyData(**currency_dict) for currency_dict in combined_currencies.values()]

    async def _get_currencies_from_db(self) -> list[CurrencyData]:
        """Fetch currencies from database as fallback."""
        try:
            currencies = await self.repository.get_all()

            if not currencies:
                logger.error("No currencies found in database for fallback")
                raise RuntimeError("No currencies available from API or database")

            # Convert ORM objects to CurrencyData objects
            currencies_data = [
                CurrencyData(
                    id=currency.id,
                    name_en=currency.name_en,
                    name_es=currency.name_es,
                    name_de=currency.name_de,
                    name_fr=currency.name_fr,
                    description_en=currency.description_en or "",
                    description_es=currency.description_es or "",
                    description_de=currency.description_de or "",
                    description_fr=currency.description_fr or "",
                    icon_url=currency.icon_url
                )
                for currency in currencies
            ]

            logger.info(f"Retrieved {len(currencies_data)} currencies from database as fallback")
            return currencies_data
        except Exception as e:
            logger.error(f"Failed to retrieve currencies from database: {e}")
            raise

    async def _sync_currencies_to_db(self, currencies_data: list[CurrencyData]) -> None:
        """Sync currencies to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = CurrenciesRepository(session)
                # Convert CurrencyData objects to dictionaries for the repository
                currencies_dicts = [currency.model_dump() for currency in currencies_data]
                await repository.upsert_batch(currencies_dicts)
                await session.commit()
            logger.info(f"Synced {len(currencies_data)} currencies to database")
        except Exception as e:
            logger.error(f"Error syncing currencies to database: {e}")
