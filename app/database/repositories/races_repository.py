from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Races
from app.database.repositories.base_repository import BaseRepository


class RacesRepository(BaseRepository[Races]):
    """Repository for managing race data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Races]:
        raise NotImplementedError("Get by ID is not implemented for races.")

    async def get_all(self) -> list[Races]:
        raise NotImplementedError("Get all is not implemented for races.")

    async def upsert(self, entity: Races) -> Races:
        raise NotImplementedError("Upsert is not implemented for races.")

    async def upsert_batch(self, races_data: list[Races]) -> None:
        """Insert or update multiple races in a batch operation."""
        if not races_data:
            return

        # Add all objects to the session
        for race in races_data:
            await self.session.merge(race)

        await self.session.flush()
