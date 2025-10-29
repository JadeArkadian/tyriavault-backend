import asyncio
from uuid import UUID

from app.api.v1.responses.wallet_response import WalletItemResponse
from app.core.logging import logger
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.repositories.wallet_repository import WalletRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client


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

    async def get_wallet(self, account_uuid: UUID) -> list[WalletItemResponse]:
        """
        Get wallet data from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            # 1. Try to get fresh data from GW2 API
            wallet_data = await self._get_wallet_from_api()

            # 2. Sync with DB in background
            asyncio.create_task(self._sync_wallet_to_db(wallet_data, account_uuid))

            # 3. Build and return response
            return await self._build_response(wallet_data)

        except Exception as e:
            logger.warning(f"Failed to fetch wallet from GW2 API: {e}. Falling back to database.")
            return await self._get_wallet_from_db(account_uuid)

    async def _get_wallet_from_api(self) -> list[dict]:
        """Fetch wallet data from GW2 API."""
        logger.info("Fetching wallet from GW2 API")
        wallet_data = await self.gw2_client.get_wallet()
        return wallet_data

    async def _get_wallet_from_db(self, account_uuid: UUID) -> list[WalletItemResponse]:
        """Fetch wallet from database as fallback."""
        try:
            logger.info(f"Fetching wallet from database for account UUID: {account_uuid}")
            wallet_entries = await self.wallet_repository.get_wallet_by_account_uuid(account_uuid)

            if not wallet_entries:
                logger.warning(f"No wallet data found in database for account: {account_uuid}")
                return []

            # Convert DB models to response format
            wallet_data = []
            for entry in wallet_entries:
                currency = entry.currency
                wallet_item = {
                    'currency_id': entry.currency_id,
                    'amount': entry.amount or 0
                }
                currency_info = {
                    'name_en': currency.name_en,
                    'name_es': currency.name_es,
                    'name_de': currency.name_de,
                    'name_fr': currency.name_fr,
                    'description_en': currency.description_en,
                    'description_es': currency.description_es,
                    'description_de': currency.description_de,
                    'description_fr': currency.description_fr,
                    'icon_url': currency.icon_url
                }
                wallet_data.append(WalletItemResponse.map_response(wallet_item, currency_info))

            logger.info(f"Retrieved {len(wallet_data)} wallet entries from database")
            return wallet_data

        except Exception as e:
            logger.error(f"Failed to retrieve wallet from database: {e}")
            raise

    async def _build_response(self, wallet_data: list[dict]) -> list[WalletItemResponse]:
        """Build the response by combining wallet data with currency information."""
        if not wallet_data:
            return []

        # Get all currency IDs from wallet data
        currency_ids = {item['id'] for item in wallet_data}

        # Fetch currency information from database
        currencies = await self.currencies_repository.get_by_ids(list(currency_ids))

        # Create a lookup dict for currencies
        currency_lookup = {currency.id: currency for currency in currencies}

        # Build responses
        responses = []
        for wallet_item in wallet_data:
            currency_id = wallet_item['id']
            currency = currency_lookup.get(currency_id)

            if not currency:
                logger.warning(f"Currency {currency_id} not found in database. Skipping wallet entry.")
                continue

            currency_info = {
                'name_en': currency.name_en,
                'name_es': currency.name_es,
                'name_de': currency.name_de,
                'name_fr': currency.name_fr,
                'description_en': currency.description_en,
                'description_es': currency.description_es,
                'description_de': currency.description_de,
                'description_fr': currency.description_fr,
                'icon_url': currency.icon_url
            }

            wallet_entry = {
                'currency_id': currency_id,
                'amount': wallet_item['value']
            }

            responses.append(WalletItemResponse.map_response(wallet_entry, currency_info))

        logger.info(f"Successfully built response with {len(responses)} wallet entries")
        return responses

    async def _sync_wallet_to_db(self, wallet_data: list[dict], account_uuid: UUID) -> None:
        """Sync wallet data to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                wallet_repository = WalletRepository(session)

                # Prepare wallet entries for batch upsert
                wallet_entries = []
                for item in wallet_data:
                    wallet_entries.append({
                        'currency_id': item['id'],
                        'game_account_uuid': account_uuid,
                        'amount': item['value']
                    })

                await wallet_repository.upsert_batch(wallet_entries)
                await session.commit()

                logger.info(f"Synced {len(wallet_entries)} wallet entries to database for account {account_uuid}")

        except Exception as e:
            logger.error(f"Error syncing wallet to database: {e}")
