from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Currencies
from app.database.repositories.base_repository import BaseRepository


class CurrenciesRepository(BaseRepository[Currencies]):
    """Repository for managing currency data synchronized from GW2 API."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Currencies]:
        raise NotImplementedError("Get by ID is not implemented for Currencies.")

    async def get_all(self) -> list[Currencies]:
        """Get all currencies."""
        result = await self.session.execute(select(Currencies))
        return list(result.scalars().all())

    async def upsert(self, entity: Currencies) -> Currencies:
        raise NotImplementedError("Upsert is not implemented for Currencies.")

    async def upsert_batch(self, currencies_data: list[Currencies]) -> None:
        """Insert or update multiple currencies in a batch operation."""
        if not currencies_data:
            return

        # Add all objects to the session
        for currency in currencies_data:
            await self.session.merge(currency)

        await self.session.flush()
