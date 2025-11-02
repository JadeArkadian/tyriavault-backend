from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Items
from app.database.repositories.base_repository import BaseRepository


class ItemsRepository(BaseRepository[Items]):
    """Repository for managing items data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Items]:
        raise NotImplementedError("Get by ID is not implemented for Items.")

    async def get_all(self) -> list[Items]:
        """Get all items."""
        result = await self.session.execute(select(Items))
        return list(result.scalars().all())

    async def upsert(self, entity: Items) -> Items:
        raise NotImplementedError("Upsert is not implemented for Items.")

    async def upsert_batch(self, items_data: list[Items]) -> None:
        """Insert or update multiple items in a batch operation."""
        if not items_data:
            return

        # Add all objects to the session
        for item in items_data:
            await self.session.merge(item)

        await self.session.flush()
