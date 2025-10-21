from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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

    async def get_all(self) -> list[Currencies]:
        """Get all currencies."""
        result = await self.session.execute(select(Currencies))
        return list(result.scalars().all())

    async def upsert(self, entity: Currencies) -> Currencies:
        """Insert or update a currency (upsert operation)."""
        merged_entity = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity

    async def upsert_batch(self, currencies_data: list[dict[str, Any]]) -> None:
        """Insert or update multiple currencies in a batch operation."""
        if not currencies_data:
            return

        stmt = pg_insert(Currencies).values(currencies_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'name_en': stmt.excluded.name_en,
                'name_es': stmt.excluded.name_es,
                'name_de': stmt.excluded.name_de,
                'name_fr': stmt.excluded.name_fr,
                'description_en': stmt.excluded.description_en,
                'description_es': stmt.excluded.description_es,
                'description_de': stmt.excluded.description_de,
                'description_fr': stmt.excluded.description_fr,
                'icon_url': stmt.excluded.icon_url
            }
        )
        await self.session.execute(stmt)
        await self.session.commit()
