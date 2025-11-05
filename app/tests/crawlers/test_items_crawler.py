from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.crawlers.items_crawler import ItemsCrawler
from app.gw2.responses.gw2api_items import GW2ApiItem


@pytest.mark.asyncio
async def test_crawl_upserts_new_items():
    """Test that the crawler upserts new items correctly."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configure session_factory to return an async context
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Repository mock
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[])
    repo_mock.upsert_batch = AsyncMock()

    # Configure GW2 client responses
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2, 3])

    async def item_details(chunk, lang):
        return [GW2ApiItem(
            id=i,
            name=f"name_{lang}_{i}",
            description=f"desc_{lang}_{i}",
            chat_link="[&AgEwMAAA]",
            icon="https://render.guildwars2.com/file/test.png",
            rarity="Rare",
            type="Weapon",
            level=80,
            vendor_value=100,
            flags=[]
        ) for i in chunk]

    gw2_client.get_item_details = AsyncMock(side_effect=item_details)

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Verify that get_all_ids was called
        repo_mock.get_all_ids.assert_awaited_once()

        # Verify that upsert_batch was called with 3 items
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 3

        # Verify that commit was called
        session_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_crawl_no_new_items():
    """Test that the crawler doesn't upsert when there are no new items."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configure session_factory to return an async context
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Repository mock
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[1, 2])
    repo_mock.upsert_batch = AsyncMock()

    # Configure GW2 client responses
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2])
    gw2_client.get_item_details = AsyncMock()

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Verify that get_all_ids was called
        repo_mock.get_all_ids.assert_awaited_once()

        # Verify that upsert_batch was NOT called (no new items)
        repo_mock.upsert_batch.assert_not_awaited()

        # Verify that commit was NOT called (no changes)
        session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_crawl_filters_existing_items():
    """Test that the crawler filters items that already exist in the database."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configure session_factory
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Repository mock - items 1 and 2 already exist
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[1, 2])
    repo_mock.upsert_batch = AsyncMock()

    # API returns items 1, 2, 3, 4
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2, 3, 4])

    async def item_details(chunk, lang):
        return [GW2ApiItem(
            id=i,
            name=f"name_{lang}_{i}",
            description=f"desc_{lang}_{i}",
            chat_link="[&AgEwMAAA]",
            icon="https://render.guildwars2.com/file/test.png",
            rarity="Rare",
            type="Weapon",
            level=80,
            vendor_value=100,
            flags=[]
        ) for i in chunk]

    gw2_client.get_item_details = AsyncMock(side_effect=item_details)

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Should only upsert items 3 and 4 (the new ones)
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 2
        assert all(item.id in [3, 4] for item in args[0])
