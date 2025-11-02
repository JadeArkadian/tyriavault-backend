from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Worlds
from app.database.repositories.base_repository import BaseRepository


class WorldsRepository(BaseRepository[Worlds]):
    """Repository for managing worlds data synchronized from GW2 API."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Worlds]:
        """Get a world by its ID."""
        result = await self.session.execute(
            select(Worlds).where(Worlds.id == _id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Worlds]:
        """Get all worlds."""
        result = await self.session.execute(select(Worlds))
        return list(result.scalars().all())

    async def upsert(self, entity: Worlds) -> Worlds:
        raise NotImplementedError("Upsert is not implemented for Worlds.")

    async def upsert_batch(self, worlds_data: list[Worlds]) -> None:
        """Insert or update multiple worlds in a batch operation."""
        if not worlds_data:
            return

            # Add all objects to the session
        for world in worlds_data:
            await self.session.merge(world)

        await self.session.flush()
