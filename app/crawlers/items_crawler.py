import asyncio
import datetime
import time

from app.core.constants import Constants
from app.core.logging import logger
from app.core.utils import chunked
from app.crawlers.base_crawler import BaseCrawler
from app.database.models import Items
from app.database.repositories.items_repository import ItemsRepository
from app.gw2.client import GW2Client


class ItemsCrawler(BaseCrawler):
    def __init__(self, gw2_client: GW2Client, item_repository: ItemsRepository):
        self.gw2_client = gw2_client
        self.item_repository = item_repository

    async def crawl(self):
        """Crawl items data from GW2 API and upsert into the database."""

        logger.info("Starting items crawl...")

        start_time = time.time()
        # Get all item IDs from GW2 API
        item_ids = await self.gw2_client.get_all_item_ids()
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
                    item_id = item.id
                    if item_id not in items_data:
                        # Initialize with common fields from first language
                        items_data[item_id] = {
                            "id": item.id,
                            "chat_link": item.chat_link,
                            "icon_url": item.icon,
                            "rarity_id": self._map_rarity_to_id(item.rarity),
                            "item_type_id": self._map_type_to_id(item.type),
                            "required_level": item.level,
                            "vendor_value": item.vendor_value or 0,
                            "flags": item.flags if item.flags else None,
                            "last_fetched": datetime.datetime.now(datetime.UTC),
                        }
                    # Add language-specific fields
                    items_data[item_id][f"name_{lang}"] = item.name
                    items_data[item_id][f"description_{lang}"] = item.description

            # Create list of Items objects
            items_list = [Items(**data) for data in items_data.values()]

            # Upsert into database
            await self.item_repository.upsert_batch(items_list)

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
