from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import HTTPStatusError, RequestError

from app.api.v1.currencies import get_currencies_info_from_api
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
def sample_currencies_db():
    """Sample currencies data from database"""

    # Create simple objects that can be serialized
    class CurrencyMock:
        def __init__(self, id, name_es, name_en, name_fr, name_de, description_es, description_en, description_fr,
                     description_de, icon_url):
            self.id = id
            self.name_es = name_es
            self.name_en = name_en
            self.name_fr = name_fr
            self.name_de = name_de
            self.description_es = description_es
            self.description_en = description_en
            self.description_fr = description_fr
            self.description_de = description_de
            self.icon_url = icon_url
            self._sa_instance_state = None  # Mock SQLAlchemy state

    currency1 = CurrencyMock(
        id=1,
        name_es="Oro",
        name_en="Gold",
        name_fr="Or",
        name_de="Gold",
        description_es="Moneda principal",
        description_en="Main currency",
        description_fr="Monnaie principale",
        description_de="Hauptwährung",
        icon_url="https://example.com/gold.png"
    )

    currency2 = CurrencyMock(
        id=2,
        name_es="Gemas",
        name_en="Gems",
        name_fr="Gemmes",
        name_de="Edelsteine",
        description_es="Moneda premium",
        description_en="Premium currency",
        description_fr="Monnaie premium",
        description_de="Premium-Währung",
        icon_url="https://example.com/gems.png"
    )

    return [currency1, currency2]


@pytest.fixture
def sample_currencies_api():
    """Sample currencies data from API"""
    return [
        {
            "id": 1,
            "name_es": "Oro",
            "name_en": "Gold",
            "name_fr": "Or",
            "name_de": "Gold",
            "description_es": "Moneda principal",
            "description_en": "Main currency",
            "description_fr": "Monnaie principale",
            "description_de": "Hauptwährung",
            "icon_url": "https://example.com/gold.png"
        },
        {
            "id": 2,
            "name_es": "Gemas",
            "name_en": "Gems",
            "name_fr": "Gemmes",
            "name_de": "Edelsteine",
            "description_es": "Moneda premium",
            "description_en": "Premium currency",
            "description_fr": "Monnaie premium",
            "description_de": "Premium-Währung",
            "icon_url": "https://example.com/gems.png"
        }
    ]


@pytest.mark.asyncio
async def test_get_currencies_with_data_in_db(mock_db_session, sample_currencies_db):
    """Test getting currencies when data exists in database"""
    # Mock the database query result
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = sample_currencies_db
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    client = TestClient(api)
    response = client.get("/api/v1/currencies/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name_es"] == "Oro"
    assert data[0]["name_en"] == "Gold"
    assert data[0]["icon_url"] == "https://example.com/gold.png"

    # Verify database was queried
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_currencies_empty_db_fetch_from_api(mock_db_session, sample_currencies_api, sample_currencies_db):
    """Test getting currencies when database is empty, should fetch from API and add to DB"""
    from fastapi_cache import FastAPICache

    # Clear cache before test
    await FastAPICache.clear()

    # Mock database to return empty on first call
    call_count = [0]

    def mock_execute_side_effect(*args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        # First call returns empty (before adding data)
        if call_count[0] == 0:
            scalars.all.return_value = []
        else:
            scalars.all.return_value = sample_currencies_db
        result.scalars.return_value = scalars
        call_count[0] += 1
        return result

    mock_db_session.execute = AsyncMock(side_effect=mock_execute_side_effect)

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    with patch('app.api.v1.currencies.get_currencies_info_from_api', new=AsyncMock(return_value=sample_currencies_api)), \
            patch('app.api.v1.currencies.GW2Client'):
        client = TestClient(api)
        response = client.get("/api/v1/currencies/")

    # Should get a successful response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name_es"] == "Oro"

    # Verify data was added to database
    assert mock_db_session.add.call_count == 2
    mock_db_session.commit.assert_called_once()

    # Verify that execute was called only once (for initial check)
    assert mock_db_session.execute.call_count == 1


@pytest.mark.asyncio
async def test_get_currencies_empty_db_api_returns_none(mock_db_session):
    """Test getting currencies when database is empty and API returns None"""
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

    with patch('app.api.v1.currencies.get_currencies_info_from_api', new=AsyncMock(return_value=None)), \
            patch('app.api.v1.currencies.GW2Client'):
        client = TestClient(api)
        response = client.get("/api/v1/currencies/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_success():
    """Test getting currencies info from API successfully"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock API responses for different languages
    mock_gw2_client.get_currencies = AsyncMock(side_effect=[
        [
            {"id": 1, "name": "Gold", "description": "Main currency", "icon": "https://example.com/gold.png"},
            {"id": 2, "name": "Gems", "description": "Premium currency", "icon": "https://example.com/gems.png"}
        ],  # English
        [
            {"id": 1, "name": "Oro", "description": "Moneda principal", "icon": "https://example.com/gold.png"},
            {"id": 2, "name": "Gemas", "description": "Moneda premium", "icon": "https://example.com/gems.png"}
        ],  # Spanish
        [
            {"id": 1, "name": "Gold", "description": "Hauptwährung", "icon": "https://example.com/gold.png"},
            {"id": 2, "name": "Edelsteine", "description": "Premium-Währung", "icon": "https://example.com/gems.png"}
        ],  # German
        [
            {"id": 1, "name": "Or", "description": "Monnaie principale", "icon": "https://example.com/gold.png"},
            {"id": 2, "name": "Gemmes", "description": "Monnaie premium", "icon": "https://example.com/gems.png"}
        ]  # French
    ])

    result = await get_currencies_info_from_api(mock_gw2_client)

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["name_en"] == "Gold"
    assert result[0]["name_es"] == "Oro"
    assert result[0]["name_de"] == "Gold"
    assert result[0]["name_fr"] == "Or"
    assert result[0]["description_en"] == "Main currency"
    assert result[0]["description_es"] == "Moneda principal"
    assert result[0]["icon_url"] == "https://example.com/gold.png"

    assert result[1]["id"] == 2
    assert result[1]["name_en"] == "Gems"
    assert result[1]["name_es"] == "Gemas"


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_multiple_currencies():
    """Test getting multiple currencies from API and combining them correctly"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Mock API responses with 3 currencies
    mock_gw2_client.get_currencies = AsyncMock(side_effect=[
        [
            {"id": 1, "name": "Gold", "description": "Main currency", "icon": "https://example.com/gold.png"},
            {"id": 4, "name": "Gems", "description": "Premium currency", "icon": "https://example.com/gems.png"},
            {"id": 5, "name": "Karma", "description": "Karma currency", "icon": "https://example.com/karma.png"}
        ],  # English
        [
            {"id": 1, "name": "Oro", "description": "Moneda principal", "icon": "https://example.com/gold.png"},
            {"id": 4, "name": "Gemas", "description": "Moneda premium", "icon": "https://example.com/gems.png"},
            {"id": 5, "name": "Karma", "description": "Moneda de karma", "icon": "https://example.com/karma.png"}
        ],  # Spanish
        [
            {"id": 1, "name": "Gold", "description": "Hauptwährung", "icon": "https://example.com/gold.png"},
            {"id": 4, "name": "Edelsteine", "description": "Premium-Währung", "icon": "https://example.com/gems.png"},
            {"id": 5, "name": "Karma", "description": "Karma-Währung", "icon": "https://example.com/karma.png"}
        ],  # German
        [
            {"id": 1, "name": "Or", "description": "Monnaie principale", "icon": "https://example.com/gold.png"},
            {"id": 4, "name": "Gemmes", "description": "Monnaie premium", "icon": "https://example.com/gems.png"},
            {"id": 5, "name": "Karma", "description": "Monnaie karma", "icon": "https://example.com/karma.png"}
        ]  # French
    ])

    result = await get_currencies_info_from_api(mock_gw2_client)

    assert len(result) == 3
    # Verify all currencies have all language names
    currency_ids = [c["id"] for c in result]
    assert 1 in currency_ids
    assert 4 in currency_ids
    assert 5 in currency_ids

    # Find karma currency and check it
    karma = next(c for c in result if c["id"] == 5)
    assert karma["name_en"] == "Karma"
    assert karma["name_es"] == "Karma"
    assert karma["name_de"] == "Karma"
    assert karma["name_fr"] == "Karma"


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_http_error():
    """Test handling HTTP error from GW2 API"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Simulate HTTP 503 error
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    http_error = HTTPStatusError("503", request=MagicMock(), response=mock_response)

    mock_gw2_client.get_currencies = AsyncMock(side_effect=http_error)

    with pytest.raises(Exception) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)

    # The function should raise an HTTPException
    from fastapi import HTTPException
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_request_error():
    """Test handling request error (connection failure) from GW2 API"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Simulate connection error
    request_error = RequestError("Connection timeout", request=MagicMock())
    mock_gw2_client.get_currencies = AsyncMock(side_effect=request_error)

    with pytest.raises(Exception) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)

    # The function should raise an HTTPException
    from fastapi import HTTPException
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert "Conection failure" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_unauthorized():
    """Test handling unauthorized error (401) from GW2 API"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Simulate HTTP 401 error
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    http_error = HTTPStatusError("401", request=MagicMock(), response=mock_response)

    mock_gw2_client.get_currencies = AsyncMock(side_effect=http_error)

    with pytest.raises(Exception) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)

    from fastapi import HTTPException
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_currencies_info_from_api_generic_exception():
    """Test handling generic exception from API"""
    mock_gw2_client = MagicMock(spec=GW2Client)

    # Simulate a generic exception
    mock_gw2_client.get_currencies = AsyncMock(side_effect=Exception("Unexpected error"))

    with pytest.raises(Exception) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)

    from fastapi import HTTPException
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "Internal error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_currencies_caching():
    """Test that currencies endpoint uses caching correctly"""
    from fastapi_cache import FastAPICache

    # Clear cache before test
    await FastAPICache.clear()

    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()

    # Create simple serializable mock
    class CurrencyMock:
        def __init__(self, id, name_es, name_en):
            self.id = id
            self.name_es = name_es
            self.name_en = name_en
            self._sa_instance_state = None

    currency1 = CurrencyMock(id=1, name_es="Oro", name_en="Gold")

    mock_scalars.all.return_value = [currency1]
    mock_result.scalars.return_value = mock_scalars
    mock_db_session.execute.return_value = mock_result

    # Override the dependency
    from app.db.dependency import get_db
    api.dependency_overrides[get_db] = lambda: mock_db_session

    client = TestClient(api)

    # First request - should hit the database
    response1 = client.get("/api/v1/currencies/")
    assert response1.status_code == status.HTTP_200_OK
    assert mock_db_session.execute.call_count == 1

    # Second request - should use cache, not hit database again
    response2 = client.get("/api/v1/currencies/")
    assert response2.status_code == status.HTTP_200_OK
    # Database execute should still be called only once (from first request)
    assert mock_db_session.execute.call_count == 1

    # Verify both responses are the same
    assert response1.json() == response2.json()
