from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
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

    async def upsert_batch(self, items_data: list[Items]) -> None:
        """Insert or update multiple items in a batch operation using PostgreSQL upsert."""
        if not items_data:
            return

        # Uggly but efficient way of doing bulk upsert with SQLAlchemy and PostgreSQL
        items_dicts = [
            {
                'id': item.id,
                'chat_link': item.chat_link,
                'name_es': item.name_es,
                'name_fr': item.name_fr,
                'name_en': item.name_en,
                'name_de': item.name_de,
                'rarity_id': item.rarity_id,
                'description_es': item.description_es,
                'icon_url': item.icon_url,
                'description_fr': item.description_fr,
                'description_en': item.description_en,
                'description_de': item.description_de,
                'item_type_id': item.item_type_id,
                'required_level': item.required_level,
                'vendor_value': item.vendor_value,
                'flags': item.flags
            }
            for item in items_data
        ]

        stmt = insert(Items).values(items_dicts)
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'chat_link': stmt.excluded.chat_link,
                'name_es': stmt.excluded.name_es,
                'name_fr': stmt.excluded.name_fr,
                'name_en': stmt.excluded.name_en,
                'name_de': stmt.excluded.name_de,
                'rarity_id': stmt.excluded.rarity_id,
                'description_es': stmt.excluded.description_es,
                'icon_url': stmt.excluded.icon_url,
                'description_fr': stmt.excluded.description_fr,
                'description_en': stmt.excluded.description_en,
                'description_de': stmt.excluded.description_de,
                'item_type_id': stmt.excluded.item_type_id,
                'required_level': stmt.excluded.required_level,
                'vendor_value': stmt.excluded.vendor_value,
                'flags': stmt.excluded.flags,
                'last_fetched': text('CURRENT_TIMESTAMP')
            }
        )

        await self.session.execute(stmt)
        await self.session.flush()
