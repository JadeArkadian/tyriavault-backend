import asyncio
import time

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.constants import Constants
from app.core.logging import logger
from app.core.utils import chunked
from app.crawlers.base_crawler import BaseCrawler
from app.database.models import Items
from app.database.repositories.items_repository import ItemsRepository
from app.gw2.client import GW2Client


class ItemsCrawler(BaseCrawler):
    def __init__(self, gw2_client: GW2Client, session_factory: async_sessionmaker):
        self.gw2_client = gw2_client
        self.session_factory = session_factory

    async def crawl(self):
        """Crawl items data from GW2 API and upsert into the database."""

        logger.info("Starting items crawl...")

        start_time = time.time()

        async with self.session_factory() as session:
            item_repository = ItemsRepository(session)

            # Get all item IDs from GW2 API
            api_item_ids = await self.gw2_client.get_all_item_ids()
            db_item_ids = set(await item_repository.get_all_ids())

            # Filter out item IDs that are already in the database
            item_ids = [item_id for item_id in api_item_ids if item_id not in db_item_ids]

            logger.info(f"Found {len(item_ids)} items to crawl.")

            # Fetch item details for every language in chunks and upsert into the database
            for chunk in chunked(item_ids, 150):
                items_merged = await asyncio.gather(
                    *(self.gw2_client.get_item_details(chunk, lang=lang) for lang in Constants.LANGS)
                )

                # Store temporary data for building Items objects
                items_data: dict[int, dict] = {}

                for lang, items in zip(Constants.LANGS, items_merged, strict=True):
                    for item in items:
                        item_id = item.get("id")
                        if item_id not in items_data:
                            # Initialize with common fields from first language
                            items_data[item_id] = {
                                "id": item.get("id"),
                                "chat_link": item.get("chat_link"),
                                "icon_url": item.get("icon"),
                                "rarity_id": self._map_rarity_to_id(item.get("rarity")),
                                "item_type_id": self._map_type_to_id(item.get("type")),
                                "required_level": item.get("level"),
                                "vendor_value": item.get("vendor_value", 0),
                                "flags": item.get("flags", None)
                            }
                        # Add language-specific fields
                        items_data[item_id][f"name_{lang}"] = item.get("name", "")
                        items_data[item_id][f"description_{lang}"] = item.get("description", "")

                # Create list of Items objects
                items_list = [Items(**data) for data in items_data.values()]

                # Upsert into database
                start_sql_time = time.time()
                await item_repository.upsert_batch(items_list)
                elapsed_sql = time.time() - start_sql_time
                logger.info(f"Upserted {len(items_list)} items in {elapsed_sql:.2f}s")
                await session.commit()

        elapsed = time.time() - start_time
        logger.info(f"Items crawl completed in {elapsed:.2f}s")

    def _map_rarity_to_id(self, rarity: str | None) -> int:
        """Map GW2 rarity string to database rarity ID."""
        rarity_map = {
            "Junk": 1,
            "Basic": 2,
            "Fine": 3,
            "Masterwork": 4,
            "Rare": 5,
            "Exotic": 6,
            "Ascended": 7,
            "Legendary": 8,
        }
        return rarity_map.get(rarity, 2) if rarity else 2  # Default to Basic

    def _map_type_to_id(self, item_type: str | None) -> int | None:
        """Map GW2 item type string to database item_type ID."""
        # TODO: Implement proper mapping once item_types table is populated
        # For now, return None to allow nullable field
        return None
