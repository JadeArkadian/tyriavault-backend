from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.api.v1.common import get_token_info_from_api
from app.gw2.client import GW2Client
from app.main import api


@pytest.mark.asyncio
class TestCommonStatusEndpoint:
    """Tests for the /common/status endpoint"""

    async def test_status_endpoint_returns_alive(self):
        """Test that status endpoint returns 'alive' with 200 status code"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/common/status")

        assert response.status_code == 200
        assert response.text == "alive"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    async def test_status_endpoint_no_authentication_required(self):
        """Test that status endpoint does not require authentication"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/common/status")

        # Should work without any authentication header
        assert response.status_code == 200
        assert response.text == "alive"


@pytest.mark.asyncio
class TestCommonTokenInfoEndpoint:
    """Tests for the /common/tokeninfo endpoint"""

    async def test_tokeninfo_success(self, mocker: MockerFixture):
        """Test successful response from GET /tokeninfo endpoint"""
        # Mock data simulating GW2 API response
        mock_token_info = {
            "id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
            "name": "My API Key",
            "permissions": ["account", "inventories", "characters", "tradingpost", "wallet"]
        }

        # Mock GW2 client
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(return_value=mock_token_info)

        # Patch GW2Client constructor
        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "api_key" in data
        assert "permissions" in data
        assert data["api_key"] == "test-api-key-12345"
        assert isinstance(data["permissions"], list)
        assert len(data["permissions"]) == 5
        assert "account" in data["permissions"]
        assert "characters" in data["permissions"]

    async def test_tokeninfo_missing_authorization_header(self):
        """Test that missing authorization header returns 422"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/common/tokeninfo")

        assert response.status_code == 422
        assert "detail" in response.json()

    async def test_tokeninfo_invalid_authorization_format(self):
        """Test that invalid authorization format returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "InvalidFormatWithoutBearer"}
            )

        assert response.status_code == 400
        assert "Invalid authorization header format" in response.json()["detail"]

    async def test_tokeninfo_invalid_authentication_scheme(self):
        """Test that non-Bearer authentication scheme returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Basic sometoken123"}
            )

        assert response.status_code == 400
        # The error message depends on how split_bearer_token handles it
        detail = response.json()["detail"]
        assert "Invalid" in detail

    async def test_tokeninfo_empty_authorization_header(self):
        """Test that empty authorization header returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": ""}
            )

        assert response.status_code == 400
        assert "Invalid authorization header format" in response.json()["detail"]

    async def test_tokeninfo_with_cache(self, mocker: MockerFixture):
        """Test that verifies cache functionality works correctly"""
        mock_token_info = {
            "id": "TEST-API-KEY",
            "name": "Test Key",
            "permissions": ["account", "characters"]
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(return_value=mock_token_info)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            # First call - should hit the API
            response1 = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer test-key-cache"}
            )
            assert response1.status_code == 200

            # Second call - should use cache
            response2 = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer test-key-cache"}
            )
            assert response2.status_code == 200

            # Verify both responses are equal
            assert response1.json() == response2.json()

            # Client should only have been called once
            assert mock_gw2_client.token_info.call_count == 1

    async def test_tokeninfo_http_401_error(self, mocker: MockerFixture):
        """Test handling of 401 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/tokeninfo")
        response = httpx.Response(401, request=request, text="Invalid access token")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer invalid-token"}
            )

        assert response.status_code == 401
        assert "Missing or invalid token" in response.json()["detail"]

    async def test_tokeninfo_http_403_error(self, mocker: MockerFixture):
        """Test handling of 403 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/tokeninfo")
        response = httpx.Response(403, request=request, text="Forbidden")
        error = httpx.HTTPStatusError("Forbidden", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer unauthorized-token"}
            )

        assert response.status_code == 403
        assert "Missing or unauthorized token" in response.json()["detail"]

    async def test_tokeninfo_http_500_error(self, mocker: MockerFixture):
        """Test handling of 500 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/tokeninfo")
        response = httpx.Response(500, request=request, text="Internal Server Error")
        error = httpx.HTTPStatusError("Server Error", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"

    async def test_tokeninfo_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Connection refused")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 503
        assert "Connection failure" in response.json()["detail"]

    async def test_tokeninfo_generic_error(self, mocker: MockerFixture):
        """Test handling of generic error"""
        error = Exception("Unexpected error")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.common.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/common/tokeninfo",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetTokenInfoFromApi:
    """Tests for the get_token_info_from_api function"""

    async def test_get_token_info_success(self, mocker: MockerFixture):
        """Test that verifies the function returns token info correctly"""
        mock_token_info = {
            "id": "API-KEY-123",
            "name": "My Test Key",
            "permissions": ["account", "characters", "inventories"]
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(return_value=mock_token_info)

        result = await get_token_info_from_api(mock_gw2_client)

        assert result == mock_token_info
        assert result["id"] == "API-KEY-123"
        assert len(result["permissions"]) == 3
        assert "account" in result["permissions"]

    async def test_get_token_info_minimal_permissions(self, mocker: MockerFixture):
        """Test with minimal permissions"""
        mock_token_info = {
            "id": "LIMITED-KEY",
            "name": "Limited Key",
            "permissions": ["account"]
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(return_value=mock_token_info)

        result = await get_token_info_from_api(mock_gw2_client)

        assert result["id"] == "LIMITED-KEY"
        assert len(result["permissions"]) == 1
        assert result["permissions"][0] == "account"

    async def test_get_token_info_all_permissions(self, mocker: MockerFixture):
        """Test with all possible permissions"""
        mock_token_info = {
            "id": "FULL-ACCESS-KEY",
            "name": "Full Access",
            "permissions": [
                "account",
                "builds",
                "characters",
                "guilds",
                "inventories",
                "progression",
                "pvp",
                "tradingpost",
                "unlocks",
                "wallet"
            ]
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(return_value=mock_token_info)

        result = await get_token_info_from_api(mock_gw2_client)

        assert result["id"] == "FULL-ACCESS-KEY"
        assert len(result["permissions"]) == 10
        assert "tradingpost" in result["permissions"]
        assert "wallet" in result["permissions"]

    async def test_get_token_info_api_error_raises_http_exception(self, mocker: MockerFixture):
        """Test that verifies API errors raise HTTPException"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/tokeninfo")
        response = httpx.Response(404, request=request, text="Not Found")
        error = httpx.HTTPStatusError("Not Found", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_token_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Not Found"

    async def test_get_token_info_401_error(self, mocker: MockerFixture):
        """Test handling of 401 unauthorized error"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/tokeninfo")
        response = httpx.Response(401, request=request, text="Invalid access token")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_token_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 401
        assert "Missing or invalid token" in exc.value.detail

    async def test_get_token_info_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Network unreachable")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.token_info = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_token_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 503
        assert "Connection failure" in exc.value.detail
