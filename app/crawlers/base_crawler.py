# app/crawlers/base.py
from abc import ABC, abstractmethod


class BaseCrawler(ABC):
    """Base class for all crawlers."""

    @abstractmethod
    async def crawl(self):
        """Crawl data from the source."""
        ...
