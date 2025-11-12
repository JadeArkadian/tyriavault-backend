import asyncio

from app.core.constants import Constants
from app.core.logging import logger
from app.database.repositories.worlds_repository import WorldsRepository
from app.database.session import async_session_maker
from app.gw2.gw2_client import GW2Client, GW2ApiError
from app.services.dtos.worlds_dto import WorldDTO


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
        self._background_tasks: set[asyncio.Task] = set()

    async def get_all_worlds(self) -> list[WorldDTO]:
        """
        Get all worlds. Strategy with Circuit Breaker:
        1 - Try API first (with timeout protection via circuit breaker)
        2 - If circuit is open or API fails, fallback to DB immediately
        3 - If API succeeds, sync to DB in background
        """
        try:
            # Try API - if circuit breaker is open, fails immediately
            worlds_data = await self._get_worlds_from_api()
            # Sync with db in background
            task = asyncio.create_task(self._sync_worlds_to_db(worlds_data))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            return worlds_data
        except GW2ApiError as e:
            # Circuit breaker open or API failed -> fast fallback to DB
            logger.info(f"GW2 API unavailable, using database fallback: {e}")
            try:
                return await self._get_worlds_from_db()
            except Exception as db_error:
                logger.error(f"Database fallback also failed: {db_error}")
                raise RuntimeError("Both API and database failed") from db_error
        except Exception as e:
            logger.error(f"Unexpected error in get_all_worlds: {e}")
            # Try DB as last resort
            try:
                return await self._get_worlds_from_db()
            except Exception as db_error:
                logger.error(f"Database fallback also failed: {db_error}")
                raise

    async def _get_worlds_from_api(self) -> list[WorldDTO]:
        """Fetch worlds from GW2 API in all supported languages and combine the data."""
        results = await asyncio.gather(
            *(self.gw2_client.get_worlds(lang=lang) for lang in Constants.LANGS)
        )

        # Store temporary data for building DTOs
        world_data: dict[int, dict[str, str]] = {}

        for lang, worlds in zip(Constants.LANGS, results, strict=True):
            for world in worlds:
                world_id = world.id
                world_data.setdefault(world_id, {})
                world_data[world_id][f"name_{lang}"] = world.name

        # Create DTOs directly from collected data
        return [
            WorldDTO(
                id=world_id,
                name_en=data["name_en"],
                name_es=data["name_es"],
                name_de=data["name_de"],
                name_fr=data["name_fr"]
            )
            for world_id, data in world_data.items()
        ]

    async def _get_worlds_from_db(self) -> list[WorldDTO]:
        """Fetch worlds from database as fallback."""
        try:
            worlds = await self.repository.get_all()

            if not worlds:
                raise ValueError("No worlds found in database")

            # Convert ORM objects to DTOs
            worlds_data = [WorldDTO.from_orm(world) for world in worlds]

            return worlds_data
        except Exception as e:
            logger.warning(f"Failed to retrieve worlds from database: {e}")
            raise

    async def _sync_worlds_to_db(self, worlds_data: list[WorldDTO]) -> None:
        """Sync worlds to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = WorldsRepository(session)
                # Convert DTOs to ORM objects for repository batch operation
                worlds_orm_list = [world.to_orm() for world in worlds_data]
                await repository.upsert_batch(worlds_orm_list)
                await session.commit()
            logger.info(f"Synced {len(worlds_data)} worlds to database")
        except Exception as e:
            logger.error(f"Error syncing worlds to database: {e}")
