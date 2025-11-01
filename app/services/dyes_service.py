import asyncio

from app.core.constants import Constants
from app.core.logging import logger
from app.core.utils import rgb_to_hex
from app.database.models import Dyes
from app.database.repositories.dyes_repository import DyesRepository
from app.database.session import async_session_maker
from app.gw2.client import GW2Client


class DyesService:
    """
    Service to manage dyes data from GW2 API and database.
    Dyes can change on some patches, so we try API first.

    Data fetch strategy: 1 - Try to get data from GW2 API
                         2 - If successful, return data and sync with DB in background
                         3 - If API fails, fallback to DB
                         4 - If both fail, raise error

    """

    def __init__(self, repository: DyesRepository, gw2_client: GW2Client):
        self.repository = repository
        self.gw2_client = gw2_client
        self._background_tasks: set[asyncio.Task] = set()

    async def get_all_dyes(self) -> list[Dyes]:
        """
        Get all dyes from GW2 API and sync with database in the background.
        If API fails, fallback to database.
        """
        try:
            dyes_data = await self._get_dyes_from_api()

            # Sync with db in background
            task = asyncio.create_task(self._sync_dyes_to_db(dyes_data))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return dyes_data
        except Exception as e:
            logger.warning(f"Failed to fetch dyes from GW2 API: {e}. Falling back to database.")
            return await self._get_dyes_from_db()

    async def _get_dyes_from_api(self) -> list[Dyes]:
        """Fetch dyes from GW2 API in all supported languages and combine the data."""
        results = await asyncio.gather(
            *(self.gw2_client.get_colors(lang=lang) for lang in Constants.LANGS)
        )

        combined_dyes: dict[int, dict[str, str | int]] = {}

        for lang, dyes in zip(Constants.LANGS, results, strict=True):
            for dye in dyes:
                dye_id = dye.id
                if dye_id not in combined_dyes:
                    combined_dyes[dye_id] = {
                        "id": dye_id,
                        "color": rgb_to_hex(dye.cloth.rgb)
                    }
                combined_dyes[dye_id][f"name_{lang}"] = dye.name

        # Convert to Dyes objects
        return [Dyes(**dye_dict) for dye_dict in combined_dyes.values()]

    async def _get_dyes_from_db(self) -> list[Dyes]:
        """Fetch dyes from database as fallback."""
        try:
            dyes = await self.repository.get_all()

            if not dyes:
                logger.error("No dyes found in database for fallback")
                raise RuntimeError("No dyes available from API or database")

            logger.info(f"Retrieved {len(dyes)} dyes from database as fallback")
            return dyes
        except Exception as e:
            logger.error(f"Failed to retrieve dyes from database: {e}")
            raise

    async def _sync_dyes_to_db(self, dyes_data: list[Dyes]) -> None:
        """Sync dyes to database using a new session for background task."""
        try:
            async with async_session_maker() as session:
                repository = DyesRepository(session)
                await repository.upsert_batch(dyes_data)
                await session.commit()
            logger.info(f"Synced {len(dyes_data)} dyes to database")
        except Exception as e:
            logger.error(f"Error syncing dyes to database: {e}")
