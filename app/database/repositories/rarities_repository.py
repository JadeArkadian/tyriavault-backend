from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Rarities
from app.database.repositories.base_repository import BaseRepository


class RaritiesRepository(BaseRepository[Rarities]):
    """Repository for managing rarities data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Rarities]:
        raise NotImplementedError("Get by ID is not implemented for rarities.")

    async def get_all(self) -> list[Rarities]:
        raise NotImplementedError("Get all is not implemented for rarities.")

    async def upsert(self, entity: Rarities) -> Rarities:
        raise NotImplementedError("Upsert is not implemented for rarities.")

    async def upsert_batch(self, rarities_data: list[Rarities]) -> None:
        """Insert or update multiple rarities in a batch operation."""
        if not rarities_data:
            return

        # Add all objects to the session
        for rarity in rarities_data:
            await self.session.merge(rarity)

        await self.session.flush()
