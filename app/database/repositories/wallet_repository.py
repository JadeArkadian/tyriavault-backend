from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Wallet
from app.database.repositories.base_repository import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    """Repository for managing wallet data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Wallet]:
        raise NotImplementedError("Get by ID is not implemented for Wallet.")

    async def get_all(self) -> list[Wallet]:
        raise NotImplementedError("Get all is not implemented for Wallet.")

    async def upsert(self, entity: Wallet) -> Wallet:
        raise NotImplementedError("Upsert is not implemented for Wallet.")

    async def get_wallet_by_account_uuid(self, uuid: UUID) -> list[Wallet]:
        """Get wallet entries by game account UUID."""
        result = await self.session.execute(
            select(Wallet)
            .options(selectinload(Wallet.currency))
            .where(Wallet.game_account_uuid == uuid)
        )
        return list(result.scalars().all())

    async def upsert_batch(self, wallet_data: list[Wallet]) -> None:
        """Insert or update multiple wallet tuples in a batch operation."""
        if not wallet_data:
            return

        # Add all objects to the session
        for wallet in wallet_data:
            await self.session.merge(wallet)

        await self.session.flush()
