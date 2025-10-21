from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Currencies
from app.database.repositories.base_repository import BaseRepository


class CurrenciesRepository(BaseRepository[Currencies]):
    """Repository for managing currency data synchronized from GW2 API."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Currencies]:
        """Get a currency by its ID."""
        result = await self.session.execute(
            select(Currencies).where(Currencies.id == _id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Currencies]:
        """Get all currencies."""
        result = await self.session.execute(select(Currencies))
        return list(result.scalars().all())

    async def upsert(self, entity: Currencies) -> Currencies:
        """Insert or update a currency (upsert operation)."""
        merged_entity = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity
