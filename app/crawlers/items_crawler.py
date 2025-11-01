import asyncio

from app.core.constants import Constants
from app.core.utils import chunked
from app.crawlers.base_crawler import BaseCrawler
from app.database.repositories.items_repository import ItemsRepository
from app.gw2.client import GW2Client


class ItemsCrawler(BaseCrawler):
    def __init__(self, gw2_client: GW2Client, item_repository: ItemsRepository):
        self.gw2_client = gw2_client
        self.item_repository = item_repository

    async def crawl(self):
        # Get all item IDs from GW2 API
        item_ids = await self.gw2_client.get_all_item_ids()

        # Fetch item details in chunks and upsert into the database
        for chunk in chunked(item_ids, 150):
            items = await asyncio.gather(
                *(self.gw2_client.get_item_details(chunk, lang=lang) for lang in Constants.LANGS)
            )

            await self.item_repository.upsert_batch(items)
