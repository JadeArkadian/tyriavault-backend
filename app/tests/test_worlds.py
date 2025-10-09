from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from fastapi import HTTPException

from app.api.v1 import worlds
from app.db.model import Worlds


@pytest_asyncio.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_worlds_from_db(mock_db):
    # Simulate worlds existing in the database
    mock_result = MagicMock()
    world_obj = Worlds(id=1, name_es="World1ES", name_en="World1EN", name_fr="World1FR", name_de="World1DE")
    mock_result.scalars.return_value.all.return_value = [world_obj]
    mock_db.execute.return_value = mock_result

    result = await worlds.get_worlds(mock_db)
    assert len(result) == 1
    assert result[0].id == world_obj.id
    assert result[0].name_es == world_obj.name_es
    assert result[0].name_en == world_obj.name_en
    assert result[0].name_fr == world_obj.name_fr
    assert result[0].name_de == world_obj.name_de


@pytest.mark.asyncio
@patch("app.api.v1.worlds.GW2Client")
@patch("app.api.v1.worlds.get_worlds_info_from_api")
async def test_get_worlds_from_api(mock_get_worlds_info_from_api, mock_GW2Client, mock_db):
    # Simulate no worlds in the database
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    # Simulate worlds returned from the API
    mock_get_worlds_info_from_api.return_value = [
        {"id": 2, "name_es": "World2ES", "name_en": "World2EN", "name_fr": "World2FR", "name_de": "World2DE"}
    ]
    # Simulate GW2Client instance
    mock_GW2Client.return_value = MagicMock()

    result = await worlds.get_worlds(mock_db)
    assert result == [
        {"id": 2, "name_es": "World2ES", "name_en": "World2EN", "name_fr": "World2FR", "name_de": "World2DE"}
    ]
    mock_db.add.assert_called()
    mock_db.commit.assert_awaited()


@pytest.mark.asyncio
@patch("app.gw2.client.GW2Client.get_worlds", new_callable=AsyncMock)
async def test_get_worlds_info_from_api_combines_languages(mock_get_worlds):
    # Simulate different responses for each language
    mock_get_worlds.side_effect = [
        [{"id": 1, "name": "WorldEN"}],
        [{"id": 1, "name": "WorldES"}],
        [{"id": 2, "name": "WorldDE"}],
        [{"id": 2, "name": "WorldFR"}]
    ]
    gw2 = MagicMock()
    gw2.get_worlds = mock_get_worlds
    result = await worlds.get_worlds_info_from_api(gw2)
    assert isinstance(result, list)
    ids = [w["id"] for w in result]
    assert set(ids) == {1, 2}


@pytest.mark.asyncio
@patch("app.gw2.client.GW2Client.get_worlds", new_callable=AsyncMock)
async def test_get_worlds_info_from_api_handles_exception(mock_get_worlds):
    # Simulate an exception from the API
    mock_get_worlds.side_effect = Exception("API error")
    gw2 = MagicMock()
    gw2.get_worlds = mock_get_worlds
    with pytest.raises(HTTPException) as exc_info:
        await worlds.get_worlds_info_from_api(gw2)
    assert exc_info.value.status_code == 500 or exc_info.value.status_code == 503
    assert "API error" in str(exc_info.value.detail)
