from sqlalchemy.ext.asyncio import async_sessionmaker

from app.crawlers.base_crawler import BaseCrawler
from app.gw2.client import GW2Client
from app.services.items_service import ItemsService


class ItemsCrawler(BaseCrawler):
    """
    Crawler for items data from GW2 API.
    This crawler delegates all business logic to ItemsService.
    """

    def __init__(self, gw2_client: GW2Client, session_factory: async_sessionmaker):
        self.gw2_client = gw2_client
        self.session_factory = session_factory

    async def crawl(self):
        """Execute items synchronization using ItemsService."""
        items_service = ItemsService(self.gw2_client, self.session_factory)
        await items_service.sync_items_from_api()
