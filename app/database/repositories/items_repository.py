from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Items
from app.database.repositories.base_repository import BaseRepository


class ItemsRepository(BaseRepository[Items]):
    """Repository for managing items data """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, _id: int) -> Optional[Items]:
        raise NotImplementedError("Get by ID is not implemented for Items.")

    async def get_all(self) -> list[Items]:
        """Get all items."""
        result = await self.session.execute(select(Items))
        return list(result.scalars().all())

    async def upsert(self, entity: Items) -> Items:
        raise NotImplementedError("Upsert is not implemented for Items.")

    async def upsert_batch(self, items_data: list[dict[str, Any]]) -> None:
        """Insert or update multiple items in a batch operation."""
        if not items_data:
            return

        stmt = pg_insert(Items).values(items_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Items.id],
            set_={
                'chat_link': stmt.excluded.chat_link,
                'name_en': stmt.excluded.name_en,
                'name_es': stmt.excluded.name_es,
                'name_de': stmt.excluded.name_de,
                'name_fr': stmt.excluded.name_fr,
                'rarity_id': stmt.excluded.rarity_id,
                'icon_url': stmt.excluded.icon_url,
                'description_en': stmt.excluded.description_en,
                'description_es': stmt.excluded.description_es,
                'description_de': stmt.excluded.description_de,
                'description_fr': stmt.excluded.description_fr,
                'item_type_id': stmt.excluded.item_type_id,
                'required_level': stmt.excluded.required_level,
                'vendor_value': stmt.excluded.vendor_value,
                'flags': stmt.excluded.flags
            }
        )
        await self.session.execute(stmt)
        await self.session.flush()
