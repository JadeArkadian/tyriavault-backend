from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Dyes
from app.database.repositories.base_repository import BaseRepository


class DyesRepository(BaseRepository[Dyes]):
    """Repository for managing dyes (colors) data synchronized from GW2 API."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Dyes]:
        raise NotImplementedError("GetByID is not implemented for Dyes.")

    async def get_all(self) -> list[Dyes]:
        """Get all dyes."""
        result = await self.session.execute(select(Dyes))
        return list(result.scalars().all())

    async def upsert(self, entity: Dyes) -> Dyes:
        raise NotImplementedError("Upsert is not implemented for Dyes.")

    async def upsert_batch(self, dyes_data: list[Dyes]) -> None:
        """Insert or update multiple dyes in a batch operation."""
        if not dyes_data:
            return

        # Add all objects to the session
        for dye in dyes_data:
            await self.session.merge(dye)

        await self.session.flush()
