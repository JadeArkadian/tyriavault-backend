from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.common import status, check_token_info
from app.db.model import ApiKeys


# Test para status()
def test_status():
    response = status()
    assert response.status_code == 200
    assert response.body == b"alive"
    assert response.media_type == "text/plain"


# Test para check_token_info: token válido en la base de datos
@pytest.mark.asyncio
async def test_check_token_info_token_in_db():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_token = "valid_token"
    mock_api_key = ApiKeys(api_key=mock_token, permissions=["account"], game_account_id=None)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_api_key
    mock_db.execute.return_value = mock_result

    with patch("app.core.utils.split_bearer_token", return_value=mock_token):
        result = await check_token_info(authorization="Bearer valid_token", db=mock_db)
        assert result == mock_api_key


# Test para check_token_info: token no está en la base de datos, pero es válido en GW2 API
@pytest.mark.asyncio
async def test_check_token_info_token_not_in_db_but_valid_in_api():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_token = "new_token"
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    mock_token_info = {"permissions": ["account"]}
    with patch("app.core.utils.split_bearer_token", return_value=mock_token), \
            patch("app.gw2.client.GW2Client.token_info", new=AsyncMock(return_value=mock_token_info)), \
            patch("app.gw2.client.get_gw2_http_client", return_value=MagicMock()):
        result = await check_token_info(authorization="Bearer new_token", db=mock_db)
        assert result.api_key == mock_token
        assert result.permissions == ["account"]


# Test para check_token_info: formato de token inválido
@pytest.mark.asyncio
async def test_check_token_info_invalid_token_format():
    mock_db = AsyncMock(spec=AsyncSession)
    with patch("app.core.utils.split_bearer_token", side_effect=ValueError("Invalid authorization header format")):
        with pytest.raises(HTTPException) as exc:
            await check_token_info(authorization="bad_header", db=mock_db)
        assert exc.value.status_code == 400
        assert "Invalid authorization header format" in exc.value.detail


# Test para check_token_info: token inválido en GW2 API (401)
@pytest.mark.asyncio
async def test_check_token_info_invalid_token_gw2():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_token = "bad_token"
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    # Simula httpx.HTTPStatusError como lo haría GW2Client.token_info
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Missing or invalid token."
    http_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
    with patch("app.core.utils.split_bearer_token", return_value=mock_token), \
            patch("app.gw2.client.GW2Client.token_info", new=AsyncMock(side_effect=http_error)), \
            patch("app.gw2.client.get_gw2_http_client", return_value=MagicMock()):
        with pytest.raises(HTTPException) as exc:
            await check_token_info(authorization="Bearer bad_token", db=mock_db)
        assert exc.value.status_code == 401


# Test para check_token_info: error de conexión a la API GW2 (simula RequestError)
@pytest.mark.asyncio
async def test_check_token_info_gw2_request_error():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_token = "bad_token"
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    request_error = httpx.RequestError("Connection failure", request=MagicMock())
    with patch("app.core.utils.split_bearer_token", return_value=mock_token), \
            patch("app.gw2.client.GW2Client.token_info", new=AsyncMock(side_effect=request_error)), \
            patch("app.gw2.client.get_gw2_http_client", return_value=MagicMock()):
        with pytest.raises(HTTPException) as exc:
            await check_token_info(authorization="Bearer bad_token", db=mock_db)
        assert exc.value.status_code == 503


# Test para check_token_info: excepción genérica en la API GW2
@pytest.mark.asyncio
async def test_check_token_info_gw2_generic_exception():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_token = "bad_token"
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    with patch("app.core.utils.split_bearer_token", return_value=mock_token), \
            patch("app.gw2.client.GW2Client.token_info", new=AsyncMock(side_effect=Exception("Internal error"))), \
            patch("app.gw2.client.get_gw2_http_client", return_value=MagicMock()):
        with pytest.raises(HTTPException) as exc:
            await check_token_info(authorization="Bearer bad_token", db=mock_db)
        assert exc.value.status_code == 500
