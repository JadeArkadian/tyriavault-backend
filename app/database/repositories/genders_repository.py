from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Genders
from app.database.repositories.base_repository import BaseRepository


class GendersRepository(BaseRepository[Genders]):
    """Repository for managing gender data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Genders]:
        raise NotImplementedError("Get by ID is not implemented for genders.")

    async def get_all(self) -> list[Genders]:
        raise NotImplementedError("Get all is not implemented for genders.")

    async def upsert(self, entity: Genders) -> Genders:
        raise NotImplementedError("Upsert is not implemented for genders.")

    async def upsert_batch(self, genders_data: list[Genders]) -> None:
        """Insert or update multiple genders in a batch operation."""
        if not genders_data:
            return

        # Add all objects to the session
        for gender in genders_data:
            await self.session.merge(gender)

        await self.session.flush()
