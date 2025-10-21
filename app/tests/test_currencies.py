import httpx
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.currencies import get_currencies, get_currencies_info_from_api
from app.db.model import Currencies


@pytest.mark.asyncio
@patch("app.api.v1.currencies.GW2Client")
async def test_get_currencies_from_api_and_store(mock_gw2_client):
    # Arrange
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    mock_api_data = [
        {"id": 1, "name_en": "Gold", "description_en": "Gold coin", "icon_url": "icon1"},
        {"id": 2, "name_en": "Silver", "description_en": "Silver coin", "icon_url": "icon2"},
    ]

    # Mock the internal function call
    with patch("app.api.v1.currencies.get_currencies_info_from_api", new_callable=AsyncMock) as mock_get_from_api:
        mock_get_from_api.return_value = mock_api_data

        # Act
        response = await get_currencies(db=mock_db)

        # Assert
        mock_get_from_api.assert_called_once()
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()
        assert len(response) == 2
        assert response[0].name_en == "Gold"


@pytest.mark.asyncio
async def test_get_currencies_from_db():
    # Arrange
    mock_db = AsyncMock()
    mock_currency_1 = Currencies(id=1, name_en="Gold", description_en="Gold coin", icon_url="icon1")
    mock_currency_2 = Currencies(id=2, name_en="Silver", description_en="Silver coin", icon_url="icon2")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_currency_1, mock_currency_2]
    mock_db.execute.return_value = mock_result

    # Act
    response = await get_currencies(db=mock_db)

    # Assert
    assert len(response) == 2
    assert response[0].id == 1
    assert response[0].name_en == "Gold"
    assert response[1].id == 2
    assert response[1].name_es is None # Testing mapping works
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
@patch("app.api.v1.currencies.asyncio.gather")
async def test_get_currencies_info_from_api_success(mock_gather):
    # Arrange
    mock_gw2_client = MagicMock()
    mock_gather.return_value = [
        [{"id": 1, "name": "Gold", "description": "desc1", "icon": "icon1"}],
        [{"id": 1, "name": "Oro", "description": "desc1_es", "icon": "icon1"}],
        [{"id": 1, "name": "Gold", "description": "desc1_de", "icon": "icon1"}],
        [{"id": 1, "name": "Or", "description": "desc1_fr", "icon": "icon1"}],
    ]

    # Act
    result = await get_currencies_info_from_api(mock_gw2_client)

    # Assert
    assert len(result) == 1
    currency = result[0]
    assert currency["id"] == 1
    assert currency["name_en"] == "Gold"
    assert currency["name_es"] == "Oro"
    assert currency["name_de"] == "Gold"
    assert currency["name_fr"] == "Or"
    assert currency["description_en"] == "desc1"
    assert currency["icon_url"] == "icon1"


@pytest.mark.asyncio
@patch("app.api.v1.currencies.asyncio.gather")
async def test_get_currencies_info_from_api_http_error(mock_gather):
    # Arrange
    mock_gw2_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_gather.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=mock_response)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
@patch("app.api.v1.currencies.asyncio.gather")
async def test_get_currencies_info_from_api_request_error(mock_gather):
    # Arrange
    mock_gw2_client = MagicMock()
    mock_gather.side_effect = httpx.RequestError("Connection failure", request=MagicMock())

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_currencies_info_from_api(mock_gw2_client)
    assert exc_info.value.status_code == 503
    assert "Connection failure" in exc_info.value.detail
