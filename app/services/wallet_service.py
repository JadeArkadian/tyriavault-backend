import asyncio
from uuid import UUID

from app.api.v1.responses.wallet_response import WalletItemResponse
from app.core.logging import logger
from app.database.models import Wallet
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.repositories.wallet_repository import WalletRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client
from app.gw2.responses import GW2ApiWalletEntry


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

    async def get_wallet(self, account_uuid: UUID) -> list[WalletItemResponse]:
        """
        Get wallet data from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            wallet_data = await self._get_wallet_from_api()
            # Sync with DB in background
            task = asyncio.create_task(self._sync_wallet_to_db(wallet_data, account_uuid))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return await self._build_response(wallet_data)

        except Exception as e:
            logger.warning(f"Failed to fetch wallet from GW2 API: {e}. Falling back to database.")
            return await self._get_wallet_from_db(account_uuid)

    async def _get_wallet_from_api(self) -> list[GW2ApiWalletEntry]:
        """Fetch wallet data from GW2 API."""
        wallet_data = await self.gw2_client.get_wallet()
        return wallet_data

    async def _get_wallet_from_db(self, account_uuid: UUID) -> list[WalletItemResponse]:
        """Fetch wallet from database as fallback."""
        try:
            wallet_entries = await self.wallet_repository.get_wallet_by_account_uuid(account_uuid)

            if not wallet_entries:
                logger.warning(f"No wallet data found in database for account: {account_uuid}")
                return []

            # Convert DB models to response format
            wallet_data = []
            for entry in wallet_entries:
                currency = entry.currency
                wallet_data.append(WalletItemResponse.map_response(entry, currency))

            logger.info(f"Retrieved {len(wallet_data)} wallet entries from database")
            return wallet_data

        except Exception as e:
            logger.error(f"Failed to retrieve wallet from database: {e}")
            raise

    async def _build_response(self, wallet_data: list[GW2ApiWalletEntry]) -> list[WalletItemResponse]:
        """Build the response by combining wallet data with currency information."""
        if not wallet_data:
            return []

        # Fetch every currency information from database
        currencies = await self.currencies_repository.get_all()

        # Create a lookup dict for currencies
        currency_lookup = {currency.id: currency for currency in currencies}

        # Build responses
        responses = []
        for wallet_item in wallet_data:
            currency_id = wallet_item.id
            currency = currency_lookup.get(currency_id)

            if not currency:
                logger.warning(f"Currency {currency_id} not found in database. Skipping wallet entry.")
                continue

            # Create a Wallet-like object for the response mapper
            wallet_entry = Wallet(
                currency_id=currency_id,
                game_account_uuid=None,  # Not needed for response
                amount=wallet_item.value
            )

            responses.append(WalletItemResponse.map_response(wallet_entry, currency))

        logger.info(f"Successfully built response with {len(responses)} wallet entries")
        return responses

    async def _sync_wallet_to_db(self, wallet_data: list[GW2ApiWalletEntry], account_uuid: UUID) -> None:
        """Sync wallet data to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                wallet_repository = WalletRepository(session)

                # Prepare wallet entries for batch upsert
                wallet_entries = []
                for item in wallet_data:
                    wallet_entries.append(Wallet(
                        currency_id=item.id,
                        game_account_uuid=account_uuid,
                        amount=item.value
                    ))

                await wallet_repository.upsert_batch(wallet_entries)
                await session.commit()

            logger.info(f"Synced {len(wallet_entries)} wallet entries to database")
        except Exception as e:
            logger.error(f"Error syncing wallet to database: {e}")
