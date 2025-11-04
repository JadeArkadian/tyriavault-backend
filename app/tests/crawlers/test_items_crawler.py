from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.crawlers.items_crawler import ItemsCrawler


@pytest.mark.asyncio
async def test_crawl_upserts_new_items():
    """Test que el crawler upserta items nuevos correctamente."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configurar el session_factory para devolver un contexto asíncrono
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock del repositorio
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[])
    repo_mock.upsert_batch = AsyncMock()

    # Configurar respuestas del GW2 client
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2, 3])

    async def item_details(chunk, lang):
        return [{"id": i, "name": f"name_{lang}_{i}", "description": f"desc_{lang}_{i}",
                 "chat_link": "cl", "icon": "url", "rarity": "Rare",
                 "type": "Weapon", "level": 80, "vendor_value": 100, "flags": []} for i in chunk]

    gw2_client.get_item_details = AsyncMock(side_effect=item_details)

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Verificar que se llamó a get_all_ids
        repo_mock.get_all_ids.assert_awaited_once()

        # Verificar que se llamó a upsert_batch con 3 items
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 3

        # Verificar que se llamó a commit
        session_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_crawl_no_new_items():
    """Test que el crawler no upserta cuando no hay items nuevos."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configurar el session_factory para devolver un contexto asíncrono
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock del repositorio
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[1, 2])
    repo_mock.upsert_batch = AsyncMock()

    # Configurar respuestas del GW2 client
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2])
    gw2_client.get_item_details = AsyncMock()

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Verificar que se llamó a get_all_ids
        repo_mock.get_all_ids.assert_awaited_once()

        # Verificar que NO se llamó a upsert_batch (no hay items nuevos)
        repo_mock.upsert_batch.assert_not_awaited()

        # Verificar que NO se llamó a commit (no hay cambios)
        session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_crawl_filters_existing_items():
    """Test que el crawler filtra items que ya existen en la base de datos."""
    gw2_client = MagicMock()
    session_mock = AsyncMock()

    # Configurar el session_factory
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=session_mock)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    # Mock del repositorio - items 1 y 2 ya existen
    repo_mock = AsyncMock()
    repo_mock.get_all_ids = AsyncMock(return_value=[1, 2])
    repo_mock.upsert_batch = AsyncMock()

    # API devuelve items 1, 2, 3, 4
    gw2_client.get_all_item_ids = AsyncMock(return_value=[1, 2, 3, 4])

    async def item_details(chunk, lang):
        return [{"id": i, "name": f"name_{lang}_{i}", "description": f"desc_{lang}_{i}",
                 "chat_link": "cl", "icon": "url", "rarity": "Rare",
                 "type": "Weapon", "level": 80, "vendor_value": 100, "flags": []} for i in chunk]

    gw2_client.get_item_details = AsyncMock(side_effect=item_details)

    with patch("app.crawlers.items_crawler.ItemsRepository", return_value=repo_mock):
        crawler = ItemsCrawler(gw2_client, session_factory)
        await crawler.crawl()

        # Solo debe upsertar los items 3 y 4 (los nuevos)
        repo_mock.upsert_batch.assert_awaited_once()
        args = repo_mock.upsert_batch.await_args[0]
        assert len(args[0]) == 2
        assert all(item.id in [3, 4] for item in args[0])


@pytest.mark.asyncio
async def test_map_rarity_to_id():
    """Test del mapeo de rareza a ID."""
    crawler = ItemsCrawler(MagicMock(), MagicMock())
    assert crawler._map_rarity_to_id("Junk") == 1
    assert crawler._map_rarity_to_id("Basic") == 2
    assert crawler._map_rarity_to_id("Fine") == 3
    assert crawler._map_rarity_to_id("Masterwork") == 4
    assert crawler._map_rarity_to_id("Rare") == 5
    assert crawler._map_rarity_to_id("Exotic") == 6
    assert crawler._map_rarity_to_id("Ascended") == 7
    assert crawler._map_rarity_to_id("Legendary") == 8
    assert crawler._map_rarity_to_id(None) == 2
    assert crawler._map_rarity_to_id("Desconocido") == 2


@pytest.mark.asyncio
async def test_map_type_to_id():
    """Test del mapeo de tipo a ID."""
    crawler = ItemsCrawler(MagicMock(), MagicMock())
    assert crawler._map_type_to_id("Weapon") is None
    assert crawler._map_type_to_id(None) is None
    assert crawler._map_type_to_id("Armor") is None
