from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import GameAccounts
from app.database.repositories.base_repository import BaseRepository


class AccountRepository(BaseRepository[GameAccounts]):
    """Repository for managing game accounts data"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[GameAccounts]:
        pass

    async def get_all(self) -> Sequence[GameAccounts]:
        pass

    async def get_by_uuid(self, uuid: UUID) -> Optional[GameAccounts]:
        """Get a game account by its UUID."""
        result = await self.session.execute(
            select(GameAccounts).where(GameAccounts.uuid == uuid)
        )
        return result.scalar_one_or_none()

    async def upsert(self, entity: GameAccounts) -> GameAccounts:
        """Insert or update a game account (upsert operation)."""
        merged_entity = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity
