from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.crawlers.items_crawler import ItemsCrawler


@pytest.mark.asyncio
async def test_crawl_calls_service():
    """Test that the crawler calls ItemsService.sync_items_from_api."""
    gw2_client = MagicMock()
    session_factory = MagicMock()

    with patch("app.crawlers.items_crawler.ItemsService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Verify that ItemsService was instantiated with correct arguments
        mock_service_class.assert_called_once_with(gw2_client, session_factory)

        # Verify that sync_items_from_api was called
        mock_service.sync_items_from_api.assert_awaited_once()


@pytest.mark.asyncio
async def test_crawl_propagates_service_exceptions():
    """Test that the crawler propagates exceptions from the service."""
    gw2_client = MagicMock()
    session_factory = MagicMock()

    with patch("app.crawlers.items_crawler.ItemsService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.sync_items_from_api = AsyncMock(side_effect=Exception("Service error"))
        mock_service_class.return_value = mock_service

        crawler = ItemsCrawler(gw2_client, session_factory)

        with pytest.raises(Exception) as exc_info:
            await crawler.crawl()

        assert str(exc_info.value) == "Service error"
