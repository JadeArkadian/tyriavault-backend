import asyncio
import time

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import settings
from app.core.constants import Constants
from app.core.logging import logger
from app.core.utils import chunked, map_rarity_to_id, map_type_to_id
from app.database.repositories.items_repository import ItemsRepository
from app.gw2.client import GW2Client
from app.services.dtos.items_dto import ItemDTO


class ItemsService:
    """
    Service to manage items data from GW2 API and database.
    Handles fetching new items from the API and syncing them with the database.
    """

    def __init__(self, gw2_client: GW2Client, session_factory: async_sessionmaker):
        self.gw2_client = gw2_client
        self.session_factory = session_factory

    async def sync_items_from_api(self) -> None:
        """
        Synchronize items from GW2 API to the database.
        Fetches all item IDs from the API, filters out existing items,
        and upserts new items in batches.
        """
        logger.info("Starting items synchronization...")
        start_time = time.time()

        async with self.session_factory() as session:
            item_repository = ItemsRepository(session)

            # Get
            # - expired item IDs
            # - all item IDs from API
            # - all item IDs from DB
            api_item_ids = await self.gw2_client.get_all_item_ids()
            db_item_ids = set(await item_repository.get_all_ids())
            expired_item_ids = await item_repository.get_expired_item_ids(settings.ITEMS_CRAWLER_FETCH_EXPIRATION_SECONDS)

            # Filter out items that already exist in the database
            new_item_ids = [item_id for item_id in api_item_ids if item_id not in db_item_ids]

            logger.info(f"Found {len(new_item_ids)} new items to sync.")
            logger.info(f"Found {len(expired_item_ids)} expired items to refresh.")

            # Combine new and expired item IDs
            ids = new_item_ids + expired_item_ids
            if not ids:
                logger.info("No new items to sync.")
                elapsed = time.time() - start_time
                logger.info(f"Items synchronization completed in {elapsed:.2f}s")
                return

            # Process items in chunks
            for chunk in chunked(ids, 175):
                # Fetch item details for all languages
                items_merged = await asyncio.gather(
                    *(self.gw2_client.get_item_details(chunk, lang=lang) for lang in Constants.LANGS)
                )

                # Build ItemDTOs
                items_dtos: dict[int, ItemDTO] = {}

                for lang, items in zip(Constants.LANGS, items_merged, strict=True):
                    for item in items:
                        item_id = item.id
                        if item_id not in items_dtos:
                            # Initialize DTO with common fields from first language
                            items_dtos[item_id] = ItemDTO(
                                id=item.id,
                                name_en=item.name,
                                name_es=item.name,
                                name_de=item.name,
                                name_fr=item.name,
                                chat_link=item.chat_link,
                                rarity_id=map_rarity_to_id(item.rarity),
                                description_en=item.description,
                                description_es=item.description,
                                description_de=item.description,
                                description_fr=item.description,
                                icon_url=item.icon,
                                item_type_id=map_type_to_id(item.type),
                                required_level=item.level,
                                vendor_value=item.vendor_value or 0,
                                details=item.details,
                                flags=item.flags
                            )
                        else:
                            # Update language-specific fields
                            dto = items_dtos[item_id]
                            if lang in Constants.LANGS:
                                setattr(dto, f"name_{lang}", item.name or "")
                                setattr(dto, f"description_{lang}", item.description)

                # Convert DTOs to ORM models
                items_list = [dto.to_orm() for dto in items_dtos.values()]

                # Upsert into database
                start_sql_time = time.time()
                await item_repository.upsert_batch(items_list)
                elapsed_sql = time.time() - start_sql_time
                logger.info(f"Upserted {len(items_list)} items in {elapsed_sql:.2f}s")
                await session.commit()

        elapsed = time.time() - start_time
        logger.info(f"Items synchronization completed in {elapsed:.2f}s")
