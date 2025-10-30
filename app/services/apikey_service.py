from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.logging import logger
from app.database.models import GameAccounts, ApiKeys
from app.database.repositories.apikeys_repository import ApikeysRepository
from app.database.repositories.worlds_repository import WorldsRepository
from app.gw2.client import GW2Client


class ApiKeyService:
    """
    Service to manage API keys validation and its registration.
    Used in every endpoint that requires an API key.
    """

    def __init__(self, api_keys_repository: ApikeysRepository, worlds_repository: WorldsRepository):
        self.api_keys_repo = api_keys_repository
        self.worlds_repo = worlds_repository

    async def get_apikey_data_from_db(self, api_key: str) -> Optional[dict]:
        api_key_record = await self.api_keys_repo.get_by_apikey(api_key)

        if not api_key_record:
            return None

        return {
            "api_key": api_key_record.api_key,
            "permissions": api_key_record.permissions or [],
            "game_account_uuid": api_key_record.game_account_uuid
        }

    async def validate_and_register(self, api_key: str) -> dict:
        """Validate the API key with GW2 API and register it in the database if valid."""

        gw2_client = GW2Client(api_key=api_key)
        try:
            # 1. Validate API Key and get permissions
            logger.info(f"Validating API key: {api_key[:8]}...")
            token_info = await gw2_client.token_info()
            permissions = token_info.get("permissions", [])

            # 2. Get account information (this gives us the UUID)
            logger.info(f"Fetching account info for API key: {api_key[:8]}...")
            account_data = await gw2_client.get_account()
            account_uuid = UUID(account_data["id"])

            # 3. Verify that world_id exists in DB (FK validation)
            world_id = account_data.get("world")
            if world_id:
                world_exists = await self.worlds_repo.get_by_id(world_id)
                if not world_exists:
                    logger.error(f"World {world_id} not found in DB for account {account_data['name']}")
                    raise RuntimeError(f"World ID {world_id} doesn't exist in database. "
                                       f"Please sync worlds table first.")

            # 4. Upsert game_account
            logger.info(f"Upserting game account: {account_data['name']}")
            game_account = GameAccounts(
                uuid=account_uuid,
                account_name=account_data["name"],
                world_id=world_id,
                creation_date=datetime.fromisoformat(account_data["created"].replace("Z", "+00:00")),
                fractal_level=account_data.get("fractal_level", 1),
                last_modified=datetime.fromisoformat(
                    account_data.get("last_modified", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
                ),
                content_access=account_data.get("access", []),
                last_fetched=datetime.now(timezone.utc)
            )

            await self.api_keys_repo.upsert_game_account(game_account)
            # 5. Upsert API key with the game_account_uuid
            logger.info(f"Upserting API key for account: {account_data['name']}")
            api_key_entity = ApiKeys(
                api_key=api_key,
                permissions=permissions,
                game_account_uuid=account_uuid,
                last_fetched=datetime.now(timezone.utc)
            )
            await self.api_keys_repo.upsert(api_key_entity)
            await self.api_keys_repo.session.commit()

            return {
                "api_key": api_key,
                "permissions": permissions,
                "game_account_uuid": account_uuid,
                "account_name": account_data["name"]
            }
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            raise
