import asyncio

from app.core.constants import Constants
from app.core.logging import logger
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.session import async_session_maker
from app.gw2.gw2_client import GW2Client, GW2ApiError
from app.services.dtos.currencies_dto import CurrencyDTO


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

    async def get_all_currencies(self) -> list[CurrencyDTO]:
        """
        Get all currencies from GW2 API and sync with database in the background.
        With Circuit Breaker: fails fast to DB when API is down.
        """
        try:
            currencies_data = await self._get_currencies_from_api()

            # Sync with db in background
            task = asyncio.create_task(self._sync_currencies_to_db(currencies_data))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return currencies_data
        except GW2ApiError as e:
            logger.info(f"GW2 API unavailable (circuit breaker or timeout), using database fallback: {e}")
            return await self._get_currencies_from_db()
        except Exception as e:
            logger.warning(f"Unexpected error fetching currencies from API: {e}. Falling back to database.")
            return await self._get_currencies_from_db()

    async def _get_currencies_from_api(self) -> list[CurrencyDTO]:
        """Fetch currencies from GW2 API in all supported languages and combine the data."""
        results = await asyncio.gather(
            *(self.gw2_client.get_currencies(lang=lang) for lang in Constants.LANGS)
        )

        # Store temporary data for building DTOs
        currency_data: dict[int, dict[str, str]] = {}

        for lang, currencies in zip(Constants.LANGS, results, strict=True):
            for currency in currencies:
                currency_id = currency.id
                currency_data.setdefault(currency_id, {"icon_url": currency.icon})
                currency_data[currency_id][f"name_{lang}"] = currency.name
                currency_data[currency_id][f"description_{lang}"] = currency.description

        # Create DTOs directly from collected data
        return [
            CurrencyDTO(
                id=currency_id,
                name_en=data.get("name_en", ""),
                name_es=data.get("name_es") or data.get("name_en", ""),
                name_de=data.get("name_de") or data.get("name_en", ""),
                name_fr=data.get("name_fr") or data.get("name_en", ""),
                description_en=data.get("description_en"),
                description_es=data.get("description_es") or data.get("description_en"),
                description_de=data.get("description_de") or data.get("description_en"),
                description_fr=data.get("description_fr") or data.get("description_en"),
                icon_url=data["icon_url"]
            )
            for currency_id, data in currency_data.items()
        ]

    async def _get_currencies_from_db(self) -> list[CurrencyDTO]:
        """Fetch currencies from database as fallback."""
        try:
            currencies = await self.repository.get_all()

            if not currencies:
                logger.error("No currencies found in database for fallback")
                raise RuntimeError("No currencies available from API or database")

            # Convert ORM objects to DTOs
            currencies_data = [CurrencyDTO.from_orm(currency) for currency in currencies]

            logger.info(f"Retrieved {len(currencies_data)} currencies from database as fallback")
            return currencies_data
        except Exception as e:
            logger.error(f"Failed to retrieve currencies from database: {e}")
            raise

    async def _sync_currencies_to_db(self, currencies_data: list[CurrencyDTO]) -> None:
        """Sync currencies to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = CurrenciesRepository(session)
                # Convert DTOs to ORM objects for repository batch operation
                currencies_orm_list = [currency.to_orm() for currency in currencies_data]
                await repository.upsert_batch(currencies_orm_list)
                await session.commit()
            logger.info(f"Synced {len(currencies_data)} currencies to database")
        except Exception as e:
            logger.error(f"Error syncing currencies to database: {e}")
