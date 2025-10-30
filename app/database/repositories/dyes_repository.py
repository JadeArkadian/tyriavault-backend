from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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

    async def upsert_batch(self, dyes_data: list[dict[str, Any]]) -> None:
        """Insert or update multiple dyes in a batch operation."""
        if not dyes_data:
            return

        stmt = pg_insert(Dyes).values(dyes_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Dyes.id],
            set_={
                'name_en': stmt.excluded.name_en,
                'name_es': stmt.excluded.name_es,
                'name_de': stmt.excluded.name_de,
                'name_fr': stmt.excluded.name_fr,
                'color': stmt.excluded.color
            }
        )
        await self.session.execute(stmt)
        await self.session.flush()
