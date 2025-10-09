from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import update

from app.crawlers.worlds_crawler import update_worlds_incremental
from app.db.model import Worlds


@pytest.mark.asyncio
async def test_update_worlds_incremental_no_api_data():
    mock_db = AsyncMock()
    with patch('app.crawlers.worlds_crawler.get_worlds_info_from_api', new=AsyncMock(return_value=[])), \
            patch('app.crawlers.worlds_crawler.GW2Client'):
        await update_worlds_incremental(mock_db)
    mock_db.execute.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_worlds_incremental_insert_new_world():
    mock_db = AsyncMock()
    mock_worlds_api = [{
        'id': 1,
        'name_es': 'Mundo ES',
        'name_fr': 'Monde FR',
        'name_en': 'World EN',
        'name_de': 'Welt DE'
    }]
    # Mock para result.scalars().all() -> []
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    with patch('app.crawlers.worlds_crawler.get_worlds_info_from_api', new=AsyncMock(return_value=mock_worlds_api)), \
            patch('app.crawlers.worlds_crawler.GW2Client'):
        await update_worlds_incremental(mock_db)
    mock_db.add.assert_called_once()
    args, kwargs = mock_db.add.call_args
    world_obj = args[0]
    assert world_obj.id == 1
    assert world_obj.name_es == 'Mundo ES'
    assert world_obj.name_fr == 'Monde FR'
    assert world_obj.name_en == 'World EN'
    assert world_obj.name_de == 'Welt DE'
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_worlds_incremental_update_existing_world():
    mock_db = AsyncMock()
    mock_worlds_api = [{
        'id': 2,
        'name_es': 'Nuevo ES',
        'name_fr': 'Nouveau FR',
        'name_en': 'New EN',
        'name_de': 'Neu DE'
    }]
    db_world = MagicMock()
    db_world.id = 2
    db_world.name_es = 'Viejo ES'
    db_world.name_fr = 'Viejo FR'
    db_world.name_en = 'Viejo EN'
    db_world.name_de = 'Viejo DE'
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [db_world]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    with patch('app.crawlers.worlds_crawler.get_worlds_info_from_api', new=AsyncMock(return_value=mock_worlds_api)), \
            patch('app.crawlers.worlds_crawler.GW2Client'):
        await update_worlds_incremental(mock_db)
    # Verifica que se llama a execute con un update correcto
    found = False
    for call in mock_db.execute.call_args_list:
        args, kwargs = call
        if args and isinstance(args[0], type(update(Worlds))):
            found = True
            break
    assert found, "No se llamó a execute con un update(Worlds)"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_worlds_incremental_no_update_needed():
    mock_db = AsyncMock()
    mock_worlds_api = [{
        'id': 3,
        'name_es': 'Igual ES',
        'name_fr': 'Igual FR',
        'name_en': 'Igual EN',
        'name_de': 'Igual DE'
    }]
    db_world = MagicMock()
    db_world.id = 3
    db_world.name_es = 'Igual ES'
    db_world.name_fr = 'Igual FR'
    db_world.name_en = 'Igual EN'
    db_world.name_de = 'Igual DE'
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [db_world]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    with patch('app.crawlers.worlds_crawler.get_worlds_info_from_api', new=AsyncMock(return_value=mock_worlds_api)), \
            patch('app.crawlers.worlds_crawler.GW2Client'):
        await update_worlds_incremental(mock_db)
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
