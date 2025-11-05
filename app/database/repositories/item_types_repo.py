from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ItemTypes
from app.database.repositories.base_repository import BaseRepository


class ItemTypesRepository(BaseRepository[ItemTypes]):
    """Repository for managing ItemTypes data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[ItemTypes]:
        raise NotImplementedError("Get by ID is not implemented for ItemTypes.")

    async def get_all(self) -> list[ItemTypes]:
        raise NotImplementedError("Get all is not implemented for ItemTypes.")

    async def upsert(self, entity: ItemTypes) -> ItemTypes:
        raise NotImplementedError("Upsert is not implemented for ItemTypes.")

    async def upsert_batch(self, itemtypes_data: list[ItemTypes]) -> None:
        """Insert or update multiple ItemTypes in a batch operation."""
        if not itemtypes_data:
            return

        # Add all objects to the session
        for it_type in itemtypes_data:
            await self.session.merge(it_type)

        await self.session.flush()
