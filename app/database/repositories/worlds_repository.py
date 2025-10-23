from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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

    async def upsert_batch(self, worlds_data: list[dict[str, Any]]) -> None:
        """Insert or update multiple worlds in a batch operation."""
        if not worlds_data:
            return

        stmt = pg_insert(Worlds).values(worlds_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Worlds.id],
            set_={
                'name_en': stmt.excluded.name_en,
                'name_es': stmt.excluded.name_es,
                'name_de': stmt.excluded.name_de,
                'name_fr': stmt.excluded.name_fr
            }
        )
        await self.session.execute(stmt)
        await self.session.flush()
