import asyncio
from datetime import datetime, timezone
from uuid import UUID

from app.api.v1.responses.account_response import AccountInfoResponse
from app.core.logging import logger
from app.database.models import GameAccounts
from app.database.repositories.account_repository import AccountRepository
from app.database.repositories.worlds_repository import WorldsRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client


class AccountService:
    """
    Service to manage account data from GW2 API and database.

    Data fetch strategy: 1 - Try to get data from GW2 API (fresh data)
                         2 - If successful, return data and sync with DB in background
                         3 - If API fails, fallback to DB
                         4 - If both fail, raise error
    """

    def __init__(self, account_repository: AccountRepository, worlds_repository: WorldsRepository, gw2_client: GW2Client):
        self.account_repository = account_repository
        self.worlds_repository = worlds_repository
        self.gw2_client = gw2_client
        self.task = None

    async def get_account_details(self, account_uuid: UUID) -> AccountInfoResponse:
        """
        Get account details from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            # 1. Try to get fresh data from GW2 API
            account_data = await self._get_account_from_api()

            # 2. Sync with DB in background
            self.task = asyncio.create_task(self._sync_account_to_db(account_data))
            
            # 3. Get world info and return response
            return await self._build_response(account_data)

        except Exception as e:
            logger.warning(f"Failed to fetch account from GW2 API: {e}. Falling back to database.")
            return await self._get_account_from_db(account_uuid)

    async def _get_account_from_api(self) -> dict:
        """Fetch account data from GW2 API."""
        logger.info("Fetching account details from GW2 API")
        account_data = await self.gw2_client.get_account()
        return account_data

    async def _get_account_from_db(self, account_uuid: UUID) -> AccountInfoResponse:
        """Fetch account from database as fallback."""
        try:
            logger.info(f"Fetching account from database for UUID: {account_uuid}")
            game_account = await self.account_repository.get_by_uuid(account_uuid)

            if not game_account:
                logger.error(f"No account found in database for UUID: {account_uuid}")
                raise RuntimeError("No account data available from API or database")

            # Convert DB model to dict format expected by map_response
            account_data = {
                "id": str(game_account.uuid),
                "name": game_account.account_name,
                "created": game_account.creation_date.isoformat(),
                "fractal_level": game_account.fractal_level,
                "access": game_account.content_access or [],
                "world": game_account.world_id
            }

            return await self._build_response(account_data)

        except Exception as e:
            logger.error(f"Failed to retrieve account from database: {e}")
            raise

    async def _build_response(self, account_data: dict) -> AccountInfoResponse:
        """Build the response by combining account data with world information."""
        world_id = account_data.get("world")
        world_info = None

        if world_id:
            logger.info(f"Fetching world info for world_id: {world_id}")
            world = await self.worlds_repository.get_by_id(world_id)
            if world:
                world_info = {
                    "name_en": world.name_en,
                    "name_es": world.name_es,
                    "name_de": world.name_de,
                    "name_fr": world.name_fr,
                }
            else:
                logger.warning(f"World {world_id} not found in database. Consider syncing worlds data.")

        response = AccountInfoResponse.map_response(account_data, world_info)
        logger.info(f"Successfully fetched account details for: {account_data.get('name')}")
        return response

    async def _sync_account_to_db(self, account_data: dict) -> None:
        """Sync account data to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = AccountRepository(session)

                # Create GameAccounts entity from API data
                game_account = GameAccounts(
                    uuid=UUID(account_data["id"]),
                    account_name=account_data["name"],
                    world_id=account_data.get("world"),
                    creation_date=datetime.fromisoformat(account_data["created"].replace("Z", "+00:00")),
                    fractal_level=account_data.get("fractal_level", 1),
                    last_modified=datetime.fromisoformat(
                        account_data.get("last_modified", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
                    ),
                    content_access=account_data.get("access", []),
                    last_fetched=datetime.now(timezone.utc)
                )

                await repository.upsert(game_account)
                logger.info(f"Synced account {account_data['name']} to database")

        except Exception as e:
            logger.error(f"Error syncing account to database: {e}")
