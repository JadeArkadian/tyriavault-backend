from uuid import UUID

from app.api.v1.responses.account_response import AccountInfoResponse
from app.core.logging import logger
from app.database.repositories.worlds_repository import WorldsRepository
from app.gw2.client import GW2Client


class AccountService:

    def __init__(self, worlds_repository: WorldsRepository, gw2_client: GW2Client):
        self.worlds_repository = worlds_repository
        self.gw2_client = gw2_client
        self.task = None

    # TODO: WIP
    async def get_account_details(self, account_uuid: UUID) -> AccountInfoResponse:
        try:
            # 1. Fetch account info from GW2 API
            logger.info(f"Fetching account details from GW2 API for UUID: {account_uuid}")
            account_data = await self.gw2_client.get_account()

            # 2. Get world information from database
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

            # 3. Map to response model
            response = AccountInfoResponse.map_response(account_data, world_info)

            logger.info(f"Successfully fetched account details for: {account_data.get('name')}")
            return response

        except Exception as e:
            logger.error(f"Error fetching account details: {e}")
            raise
