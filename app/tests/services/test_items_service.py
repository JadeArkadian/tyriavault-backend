from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.gw2.responses.gw2api_items import GW2ApiItem
from app.services.items_service import ItemsService


@pytest.mark.asyncio
async def test_sync_items_from_api_with_new_items():
    """Test that sync_items_from_api correctly syncs new items."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock repository
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

    with patch("app.services.items_service.ItemsRepository", return_value=repo_mock):
        service = ItemsService(gw2_client, session_factory)
        await service.sync_items_from_api()

        # Verify that get_all_ids was called
        repo_mock.get_all_ids.assert_awaited_once()

        # Verify that upsert_batch was called with 3 items
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 3

        # Verify that commit was called
        session_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_items_from_api_with_no_new_items():
    """Test that sync_items_from_api handles no new items correctly."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock repository
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[1, 2])
    repo_mock.upsert_batch = AsyncMock()

    # Configure GW2 client responses
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2])
    gw2_client.get_item_details = AsyncMock()

    with patch("app.services.items_service.ItemsRepository", return_value=repo_mock):
        service = ItemsService(gw2_client, session_factory)
        await service.sync_items_from_api()

        # Verify that get_all_ids was called
        repo_mock.get_all_ids.assert_awaited_once()

        # Verify that upsert_batch was NOT called (no new items)
        repo_mock.upsert_batch.assert_not_awaited()

        # Verify that commit was NOT called (no changes)
        session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_items_from_api_filters_existing_items():
    """Test that sync_items_from_api filters out existing items."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock repository - items 1 and 2 already exist
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

    with patch("app.services.items_service.ItemsRepository", return_value=repo_mock):
        service = ItemsService(gw2_client, session_factory)
        await service.sync_items_from_api()

        # Should only upsert items 3 and 4 (the new ones)
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 2
        assert all(item.id in [3, 4] for item in args[0])


@pytest.mark.asyncio
async def test_map_rarity_to_id():
    """Test rarity to ID mapping."""
    service = ItemsService(MagicMock(), MagicMock())
    assert service._map_rarity_to_id("Junk") == 1
    assert service._map_rarity_to_id("Basic") == 2
    assert service._map_rarity_to_id("Fine") == 3
    assert service._map_rarity_to_id("Masterwork") == 4
    assert service._map_rarity_to_id("Rare") == 5
    assert service._map_rarity_to_id("Exotic") == 6
    assert service._map_rarity_to_id("Ascended") == 7
    assert service._map_rarity_to_id("Legendary") == 8
    assert service._map_rarity_to_id(None) == 2
    assert service._map_rarity_to_id("Unknown") == 2


@pytest.mark.asyncio
async def test_map_type_to_id():
    """Test type to ID mapping."""
    service = ItemsService(MagicMock(), MagicMock())
    assert service._map_type_to_id("Armor") == 1
    assert service._map_type_to_id("Weapon") == 19
    assert service._map_type_to_id("Consumable") == 4
    assert service._map_type_to_id(None) == 0
    assert service._map_type_to_id("Unknown") == 0
