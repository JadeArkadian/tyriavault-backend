from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import update

from app.crawlers.currencies_crawler import update_currencies_incremental
from app.db.model import Currencies


@pytest.mark.asyncio
async def test_update_currencies_incremental_no_api_data():
    """Test cuando la API no devuelve datos de currencies"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api', new=AsyncMock(return_value=[])), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    mock_db.execute.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_currencies_incremental_no_api_data_none():
    """Test cuando la API devuelve None"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api', new=AsyncMock(return_value=None)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    mock_db.execute.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_update_currencies_incremental_insert_new_currency():
    """Test inserción de una nueva currency en la base de datos"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [{
        'id': 1,
        'name_es': 'Oro',
        'name_fr': 'Or',
        'name_en': 'Gold',
        'name_de': 'Gold',
        'icon_url': 'https://example.com/gold.png',
        'description_es': 'Moneda principal',
        'description_fr': 'Monnaie principale',
        'description_en': 'Main currency',
        'description_de': 'Hauptwährung'
    }]

    # Mock para no tener currencies existentes en DB
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    mock_db.add.assert_called_once()
    args, kwargs = mock_db.add.call_args
    currency_obj = args[0]
    assert currency_obj.id == 1
    assert currency_obj.name_es == 'Oro'
    assert currency_obj.name_fr == 'Or'
    assert currency_obj.name_en == 'Gold'
    assert currency_obj.name_de == 'Gold'
    assert currency_obj.icon_url == 'https://example.com/gold.png'
    assert currency_obj.description_es == 'Moneda principal'
    assert currency_obj.description_fr == 'Monnaie principale'
    assert currency_obj.description_en == 'Main currency'
    assert currency_obj.description_de == 'Hauptwährung'
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_currencies_incremental_insert_multiple_currencies():
    """Test inserción de múltiples currencies nuevas"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [
        {
            'id': 1,
            'name_es': 'Oro',
            'name_fr': 'Or',
            'name_en': 'Gold',
            'name_de': 'Gold',
            'icon_url': 'https://example.com/gold.png',
            'description_es': 'Moneda principal',
            'description_fr': 'Monnaie principale',
            'description_en': 'Main currency',
            'description_de': 'Hauptwährung'
        },
        {
            'id': 2,
            'name_es': 'Karma',
            'name_fr': 'Karma',
            'name_en': 'Karma',
            'name_de': 'Karma',
            'icon_url': 'https://example.com/karma.png',
            'description_es': 'Moneda de karma',
            'description_fr': 'Monnaie de karma',
            'description_en': 'Karma currency',
            'description_de': 'Karma-Währung'
        }
    ]

    # Mock para no tener currencies existentes en DB
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    assert mock_db.add.call_count == 2
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_currencies_incremental_update_existing_currency():
    """Test actualización de una currency existente cuando cambia algún campo"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [{
        'id': 2,
        'name_es': 'Gemas Actualizado',
        'name_fr': 'Gemmes Nouveau',
        'name_en': 'Gems Updated',
        'name_de': 'Edelsteine Aktualisiert',
        'icon_url': 'https://example.com/gems_new.png',
        'description_es': 'Descripción nueva',
        'description_fr': 'Description nouvelle',
        'description_en': 'New description',
        'description_de': 'Neue Beschreibung'
    }]

    db_currency = MagicMock()
    db_currency.id = 2
    db_currency.name_es = 'Gemas'
    db_currency.name_fr = 'Gemmes'
    db_currency.name_en = 'Gems'
    db_currency.name_de = 'Edelsteine'
    db_currency.icon_url = 'https://example.com/gems.png'
    db_currency.description_es = 'Descripción vieja'
    db_currency.description_fr = 'Description ancienne'
    db_currency.description_en = 'Old description'
    db_currency.description_de = 'Alte Beschreibung'

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [db_currency]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    # Verifica que se llama a execute con un update correcto
    found = False
    for call in mock_db.execute.call_args_list:
        args, kwargs = call
        if args and isinstance(args[0], type(update(Currencies))):
            found = True
            break
    assert found, "No se llamó a execute con un update(Currencies)"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_currencies_incremental_no_update_needed():
    """Test cuando no hay cambios necesarios en las currencies existentes"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [{
        'id': 3,
        'name_es': 'Laureles',
        'name_fr': 'Lauriers',
        'name_en': 'Laurels',
        'name_de': 'Lorbeer',
        'icon_url': 'https://example.com/laurels.png',
        'description_es': 'Descripción igual',
        'description_fr': 'Description égale',
        'description_en': 'Same description',
        'description_de': 'Gleiche Beschreibung'
    }]

    db_currency = MagicMock()
    db_currency.id = 3
    db_currency.name_es = 'Laureles'
    db_currency.name_fr = 'Lauriers'
    db_currency.name_en = 'Laurels'
    db_currency.name_de = 'Lorbeer'
    db_currency.icon_url = 'https://example.com/laurels.png'
    db_currency.description_es = 'Descripción igual'
    db_currency.description_fr = 'Description égale'
    db_currency.description_en = 'Same description'
    db_currency.description_de = 'Gleiche Beschreibung'

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [db_currency]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_currencies_incremental_mixed_operations():
    """Test con operaciones mixtas: insertar nuevas y actualizar existentes"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [
        {
            'id': 1,
            'name_es': 'Gemas Actualizado',
            'name_fr': 'Gemmes Nouveau',
            'name_en': 'Gems Updated',
            'name_de': 'Edelsteine Aktualisiert',
            'icon_url': 'https://example.com/gems_new.png',
            'description_es': 'Nueva descripción',
            'description_fr': 'Nouvelle description',
            'description_en': 'New description',
            'description_de': 'Neue Beschreibung'
        },
        {
            'id': 2,
            'name_es': 'Oro Nuevo',
            'name_fr': 'Or Nouveau',
            'name_en': 'New Gold',
            'name_de': 'Neues Gold',
            'icon_url': 'https://example.com/gold_new.png',
            'description_es': 'Moneda nueva',
            'description_fr': 'Nouvelle monnaie',
            'description_en': 'New currency',
            'description_de': 'Neue Währung'
        }
    ]

    db_currency = MagicMock()
    db_currency.id = 1
    db_currency.name_es = 'Gemas'
    db_currency.name_fr = 'Gemmes'
    db_currency.name_en = 'Gems'
    db_currency.name_de = 'Edelsteine'
    db_currency.icon_url = 'https://example.com/gems.png'
    db_currency.description_es = 'Vieja descripción'
    db_currency.description_fr = 'Ancienne description'
    db_currency.description_en = 'Old description'
    db_currency.description_de = 'Alte Beschreibung'

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [db_currency]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    # Verifica que se insertó una nueva currency
    mock_db.add.assert_called_once()
    # Verifica que se actualizó la existente
    found = False
    for call in mock_db.execute.call_args_list:
        args, kwargs = call
        if args and isinstance(args[0], type(update(Currencies))):
            found = True
            break
    assert found, "No se llamó a execute con un update(Currencies)"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_currencies_incremental_with_empty_fields():
    """Test inserción de currency con campos opcionales vacíos"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()

    mock_currencies_api = [{
        'id': 5,
        'name_es': 'Token',
        'name_en': 'Token',
        # Sin name_fr, name_de, icon_url, descriptions
    }]

    # Mock para no tener currencies existentes en DB
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch('app.crawlers.currencies_crawler.get_currencies_info_from_api',
               new=AsyncMock(return_value=mock_currencies_api)), \
            patch('app.crawlers.currencies_crawler.GW2Client'):
        await update_currencies_incremental(mock_db)

    mock_db.add.assert_called_once()
    args, kwargs = mock_db.add.call_args
    currency_obj = args[0]
    assert currency_obj.id == 5
    assert currency_obj.name_es == 'Token'
    assert currency_obj.name_en == 'Token'
    assert currency_obj.name_fr == ''
    assert currency_obj.name_de == ''
    assert currency_obj.icon_url == ''
    assert currency_obj.description_es == ''
    assert currency_obj.description_fr == ''
    assert currency_obj.description_en == ''
    assert currency_obj.description_de == ''
    mock_db.commit.assert_called_once()
