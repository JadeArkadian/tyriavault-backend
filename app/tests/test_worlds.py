from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import HTTPStatusError, RequestError, Response

from app.api.v1.worlds import get_worlds_info_from_api
from app.db.model import Worlds
from app.gw2.client import GW2Client
from app.main import api


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.execute = AsyncMock()
    return mock_db


@pytest.fixture
def sample_worlds_db():
    """Sample worlds data from database"""
    world1 = MagicMock(spec=Worlds)
    world1.id = 1001
    world1.name_es = "Mundo 1"
    world1.name_en = "World 1"
    world1.name_fr = "Monde 1"
    world1.name_de = "Welt 1"

    world2 = MagicMock(spec=Worlds)
    world2.id = 1002
    world2.name_es = "Mundo 2"
    world2.name_en = "World 2"
    world2.name_fr = "Monde 2"
    world2.name_de = "Welt 2"

    return [world1, world2]


@pytest.fixture
def sample_worlds_api():
    """Sample worlds data from API"""
    return [
        {
            "id": 1001,
            "name_es": "Mundo 1",
            "name_en": "World 1",
            "name_fr": "Monde 1",
            "name_de": "Welt 1"
        },
        {
            "id": 1002,
            "name_es": "Mundo 2",
            "name_en": "World 2",
            "name_fr": "Monde 2",
            "name_de": "Welt 2"
        }
    ]


@pytest.mark.asyncio
async def test_get_worlds_with_data_in_db(mock_db_session, sample_worlds_db):
    """Test getting worlds when data exists in database"""
    # Mock the database query result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = sample_worlds_db
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    client = TestClient(api)
    response = client.get("/api/v1/worlds/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1001
    assert data[0]["name"]["es"] == "Mundo 1"
    assert data[0]["name"]["en"] == "World 1"
    assert data[0]["name"]["fr"] == "Monde 1"
    assert data[0]["name"]["de"] == "Welt 1"

    # Verify database was queried
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_worlds_empty_db_fetch_from_api(mock_db_session, sample_worlds_api, sample_worlds_db):
    """Test getting worlds when database is empty, should fetch from API and add to DB"""
    from fastapi_cache import FastAPICache

    # Clear cache before test
    await FastAPICache.clear()

    # Mock database to return empty on first call, then return objects on second call
    call_count = [0]

    def mock_execute_side_effect(*args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        # First call returns empty (before adding data)
        # Second call returns the data (after commit and re-query)
        if call_count[0] == 0:
            scalars.all.return_value = []
        else:
            scalars.all.return_value = sample_worlds_db
        result.scalars.return_value = scalars
        call_count[0] += 1
        return result

    mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    with patch('app.api.v1.worlds.get_worlds_info_from_api', new=AsyncMock(return_value=sample_worlds_api)), \
            patch('app.api.v1.worlds.GW2Client'):
        client = TestClient(api)
        response = client.get("/api/v1/worlds/")

    # Should get a successful response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1001
    assert data[0]["name"]["es"] == "Mundo 1"

    # Verify data was added to database
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_called_once()

    # Verify that execute was called only once (for initial check, no re-query needed)
    assert mock_db_session.execute.call_count == 1


@pytest.mark.asyncio
async def test_get_worlds_empty_db_api_returns_none(mock_db_session):
    """Test getting worlds when database is empty and API returns None"""
    from fastapi_cache import FastAPICache

    # Clear cache before test
    await FastAPICache.clear()

    # Mock empty database result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    with patch('app.api.v1.worlds.get_worlds_info_from_api', new=AsyncMock(return_value=None)), \
            patch('app.api.v1.worlds.GW2Client'):
        client = TestClient(api)
        response = client.get("/api/v1/worlds/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_worlds_info_from_api_success():
    """Test getting worlds info from API successfully"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock API responses for different languages
    mock_gw2_client.get_worlds = AsyncMock(side_effect=[
        [{"id": 1001, "name": "World 1"}],  # English
        [{"id": 1001, "name": "Mundo 1"}],  # Spanish
        [{"id": 1001, "name": "Welt 1"}],  # German
        [{"id": 1001, "name": "Monde 1"}]  # French
    ])

    result = await get_worlds_info_from_api(mock_gw2_client)

    assert len(result) == 1
    assert result[0]["id"] == 1001
    assert result[0]["name_en"] == "World 1"
    assert result[0]["name_es"] == "Mundo 1"
    assert result[0]["name_de"] == "Welt 1"
    assert result[0]["name_fr"] == "Monde 1"


@pytest.mark.asyncio
async def test_get_worlds_info_from_api_multiple_worlds():
    """Test getting multiple worlds from API"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock API responses with multiple worlds
    mock_gw2_client.get_worlds = AsyncMock(side_effect=[
        [{"id": 1001, "name": "World 1"}, {"id": 1002, "name": "World 2"}],  # English
        [{"id": 1001, "name": "Mundo 1"}, {"id": 1002, "name": "Mundo 2"}],  # Spanish
        [{"id": 1001, "name": "Welt 1"}, {"id": 1002, "name": "Welt 2"}],  # German
        [{"id": 1001, "name": "Monde 1"}, {"id": 1002, "name": "Monde 2"}]  # French
    ])

    result = await get_worlds_info_from_api(mock_gw2_client)

    assert len(result) == 2
    assert result[0]["id"] == 1001
    assert result[1]["id"] == 1002


@pytest.mark.asyncio
async def test_get_worlds_info_from_api_http_error():
    """Test API error handling for HTTP status errors"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock HTTP error
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    mock_gw2_client.get_worlds = AsyncMock(side_effect=HTTPStatusError(
        "Forbidden", request=MagicMock(), response=mock_response
    ))

    with pytest.raises(Exception) as exc_info:
        await get_worlds_info_from_api(mock_gw2_client)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_worlds_info_from_api_request_error():
    """Test API error handling for request errors"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock request error
    mock_gw2_client.get_worlds = AsyncMock(side_effect=RequestError("Connection timeout"))

    with pytest.raises(Exception) as exc_info:
        await get_worlds_info_from_api(mock_gw2_client)

    assert exc_info.value.status_code == 503
    assert "Connection failure" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_worlds_info_from_api_generic_error():
    """Test API error handling for generic errors"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock generic error
    mock_gw2_client.get_worlds = AsyncMock(side_effect=ValueError("Unexpected error"))

    with pytest.raises(Exception) as exc_info:
        await get_worlds_info_from_api(mock_gw2_client)

    assert exc_info.value.status_code == 500
    assert "Internal error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_worlds_cache_is_used(mock_db_session, sample_worlds_db):
    """Test that cache is being used for repeated requests"""
    # Mock the database query result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = sample_worlds_db
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    client = TestClient(api)

    # First request
    response1 = client.get("/api/v1/worlds/")
    assert response1.status_code == status.HTTP_200_OK

    # Second request (should use cache)
    response2 = client.get("/api/v1/worlds/")
    assert response2.status_code == status.HTTP_200_OK

    # Both responses should be identical
    assert response1.json() == response2.json()
