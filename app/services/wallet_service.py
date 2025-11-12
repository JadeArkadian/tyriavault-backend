import asyncio
from uuid import UUID

from app.core.logging import logger
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.repositories.wallet_repository import WalletRepository
from app.database.session import async_session_maker
from app.gw2.gw2_client import GW2Client, GW2ApiError
from app.gw2.responses import GW2ApiWalletEntry
from app.services.dtos.wallet_dto import WalletItemDTO


class WalletService:
    """
    Service to manage wallet data from GW2 API and database.

    Data fetch strategy: 1 - Try to get data from GW2 API (fresh data)
                         2 - If successful, return data and sync with DB in background
                         3 - If API fails, fallback to DB
                         4 - If both fail, raise error
    """

    def __init__(
            self,
            wallet_repository: WalletRepository,
            currencies_repository: CurrenciesRepository,
            gw2_client: GW2Client
    ):
        self.wallet_repository = wallet_repository
        self.currencies_repository = currencies_repository
        self.gw2_client = gw2_client
        self._background_tasks: set[asyncio.Task] = set()

    async def get_wallet(self, account_uuid: UUID) -> list[WalletItemDTO]:
        """
        Get wallet data from GW2 API and sync with database in the background.
        With Circuit Breaker: fails fast to DB when API is down.
        """
        try:
            wallet_data = await self._get_wallet_from_api()
            # Sync with DB in background
            task = asyncio.create_task(self._sync_wallet_to_db(wallet_data, account_uuid))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return await self._build_response(wallet_data)

        except GW2ApiError as e:
            logger.info(f"GW2 API unavailable (circuit breaker or timeout), using database fallback: {e}")
            return await self._get_wallet_from_db(account_uuid)
        except Exception as e:
            logger.warning(f"Unexpected error fetching wallet from API: {e}. Falling back to database.")
            return await self._get_wallet_from_db(account_uuid)

    async def _get_wallet_from_api(self) -> list[GW2ApiWalletEntry]:
        """Fetch wallet data from GW2 API."""
        wallet_data = await self.gw2_client.get_wallet()
        return wallet_data

    async def _get_wallet_from_db(self, account_uuid: UUID) -> list[WalletItemDTO]:
        """Fetch wallet from database as fallback."""
        try:
            wallet_entries = await self.wallet_repository.get_wallet_by_account_uuid(account_uuid)

            if not wallet_entries:
                logger.warning(f"No wallet data found in database for account: {account_uuid}")
                return []

            # Convert DB models to DTOs
            wallet_data = [
                WalletItemDTO.from_orm_with_currency(entry, entry.currency)
                for entry in wallet_entries
            ]

            logger.info(f"Retrieved {len(wallet_data)} wallet entries from database")
            return wallet_data

        except Exception as e:
            logger.error(f"Failed to retrieve wallet from database: {e}")
            raise

    async def _build_response(self, wallet_data: list[GW2ApiWalletEntry]) -> list[WalletItemDTO]:
        """Build the response by combining wallet data with currency information."""
        if not wallet_data:
            return []

        # Fetch every currency information from database
        currencies = await self.currencies_repository.get_all()

        # Create a lookup dict for currencies
        currency_lookup = {currency.id: currency for currency in currencies}

        # Build DTOs
        responses = []
        for wallet_item in wallet_data:
            currency_id = wallet_item.id
            currency = currency_lookup.get(currency_id)

            if not currency:
                logger.warning(f"Currency {currency_id} not found in database. Skipping wallet entry.")
                continue

            dto = WalletItemDTO.from_api_with_currency(wallet_item, currency)
            responses.append(dto)

        logger.info(f"Successfully built response with {len(responses)} wallet entries")
        return responses

    async def _sync_wallet_to_db(self, wallet_data: list[GW2ApiWalletEntry], account_uuid: UUID) -> None:
        """Sync wallet data to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                wallet_repository = WalletRepository(session)
                currencies_repository = CurrenciesRepository(session)

                # Get currencies to build DTOs
                currencies = await currencies_repository.get_all()
                currency_lookup = {currency.id: currency for currency in currencies}

                # Convert API data to ORM objects
                wallet_orm_list = []
                for item in wallet_data:
                    currency = currency_lookup.get(item.id)
                    if currency:
                        dto = WalletItemDTO.from_api_with_currency(item, currency)
                        wallet_orm = dto.to_wallet_orm(account_uuid)
                        wallet_orm_list.append(wallet_orm)

                await wallet_repository.upsert_batch(wallet_orm_list)
                await session.commit()

            logger.info(f"Synced {len(wallet_orm_list)} wallet entries to database")
        except Exception as e:
            logger.error(f"Error syncing wallet to database: {e}")
