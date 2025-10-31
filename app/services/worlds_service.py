import asyncio
from typing import Any

from app.core.constants import Constants
from app.core.logging import logger
from app.database.repositories.worlds_repository import WorldsRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client


class WorldsService:
    """
    Service to manage worlds data from GW2 API and database.
    Worlds are very unlikely to change, so we try DB first.

    Data fetch strategy: 1 - Try to get data from DB
                         2 - If empty or unsuccessful, try to get data from GW2 API
                         3 - If API successful, return data and sync with DB in background
                         4 - If both fail, raise error
    """

    def __init__(self, repository: WorldsRepository, gw2_client: GW2Client):
        self.repository = repository
        self.gw2_client = gw2_client

    async def get_all_worlds(self) -> list[dict]:
        """
        Get all worlds from database. If DB is empty, fetch from GW2 API and sync with database in the background.
        """
        try:
            worlds_data = await self._get_worlds_from_db()
            return worlds_data
        except Exception as e:
            logger.warning(f"No data in DB or failed to fetch worlds from DB: {e}. Falling back to GW2 API.")
            worlds_data = await self._get_worlds_from_api()
            # Sync with db in background
            asyncio.create_task(self._sync_worlds_to_db(worlds_data))
            return worlds_data

    async def _get_worlds_from_api(self) -> list[dict]:
        """Fetch worlds from GW2 API in all supported languages and combine the data."""
        results = await asyncio.gather(
            *(self.gw2_client.get_worlds(lang=lang) for lang in Constants.LANGS)
        )

        combined_worlds: dict[int, dict[str, Any]] = {}

        for lang, worlds in zip(Constants.LANGS, results, strict=True):
            for world in worlds:
                world_id = world["id"]
                if world_id not in combined_worlds:
                    combined_worlds[world_id] = {
                        "id": world_id,
                    }
                combined_worlds[world_id][f"name_{lang}"] = world["name"]
        return list(combined_worlds.values())

    async def _get_worlds_from_db(self) -> list[dict]:
        """Fetch worlds from database as fallback."""
        try:
            worlds = await self.repository.get_all()

            if not worlds:
                raise ValueError("No worlds found in database")

            # Convert ORM objects to dictionaries
            worlds_data = []
            for world in worlds:
                worlds_data.append({
                    "id": world.id,
                    "name_en": world.name_en,
                    "name_es": world.name_es,
                    "name_de": world.name_de,
                    "name_fr": world.name_fr,
                })

            return worlds_data
        except Exception as e:
            logger.warning(f"Failed to retrieve worlds from database: {e}")
            raise

    async def _sync_worlds_to_db(self, worlds_data: list[dict]) -> None:
        """Sync worlds to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = WorldsRepository(session)
                await repository.upsert_batch(worlds_data)
                await session.commit()
            logger.info(f"Synced {len(worlds_data)} worlds to database")
        except Exception as e:
            logger.error(f"Error syncing worlds to database: {e}")
