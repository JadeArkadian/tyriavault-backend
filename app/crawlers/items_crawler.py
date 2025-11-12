from sqlalchemy.ext.asyncio import async_sessionmaker

from app.crawlers.base_crawler import BaseCrawler
from app.gw2.gw2_crawler_client import GW2CrawlerClient
from app.services.items_service import ItemsService


class ItemsCrawler(BaseCrawler):
    """
    Crawler for items data from GW2 API.
    This crawler delegates all business logic to ItemsService.
    Uses GW2CrawlerClient for persistent retries without circuit breaker.
    """

    def __init__(self, gw2_client: GW2CrawlerClient, session_factory: async_sessionmaker):
        self.gw2_client = gw2_client
        self.session_factory = session_factory

    async def crawl(self):
        """Execute items synchronization using ItemsService."""
        items_service = ItemsService(self.gw2_client, self.session_factory)
        await items_service.sync_items_from_api()
