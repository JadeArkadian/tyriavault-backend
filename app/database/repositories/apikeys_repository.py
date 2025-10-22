from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApiKeys, GameAccounts
from app.database.repositories.base_repository import BaseRepository


class ApikeysRepository(BaseRepository[ApiKeys]):
    """Repository for managing apikeys data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[ApiKeys]:
        """Get an apikey by its ID."""
        result = await self.session.execute(
            select(ApiKeys).where(ApiKeys.id == _id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[ApiKeys]:
        """Get all apikeys."""
        result = await self.session.execute(select(ApiKeys))
        return list(result.scalars().all())

    async def upsert(self, entity: ApiKeys) -> ApiKeys:
        """Insert or update an apikey (upsert operation)."""
        merged_entity = await self.session.merge(entity)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity

    async def get_by_apikey(self, apikey: str) -> Optional[ApiKeys]:
        """Get an apikey by its ApiKey."""
        result = await self.session.execute(
            select(ApiKeys).where(ApiKeys.api_key == apikey)
        )
        return result.scalar_one_or_none()

    async def upsert_game_account(self, game_account: GameAccounts) -> GameAccounts:
        """Insert or update a game account."""
        merged_entity = await self.session.merge(game_account)
        await self.session.commit()
        await self.session.refresh(merged_entity)
        return merged_entity
