from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.api.v1.account import get_account_info_from_api
from app.gw2.client import GW2Client
from app.main import api


@pytest.mark.asyncio
class TestAccountEndpoint:
    """Tests for the /account endpoint"""

    async def test_account_details_success(self, mocker: MockerFixture):
        """Test successful response from GET /account endpoint"""
        # Mock data simulating GW2 API response
        mock_account_info = {
            "id": "12345678-1234-1234-1234-123456789012",
            "name": "Player.1234",
            "world": 2001,
            "created": "2012-08-28T00:00:00Z",
            "access": ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"],
            "fractal_level": 100
        }

        # Mock GW2 client
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            [{"id": 2001, "name": "Anvil Rock"}, {"id": 2002, "name": "Borlis Pass"}],
            [{"id": 2001, "name": "Roca del Yunque"}, {"id": 2002, "name": "Paso de Borlis"}],
            [{"id": 2001, "name": "Ambossstein"}, {"id": 2002, "name": "Borlispass"}],
            [{"id": 2001, "name": "Roche de l'Enclume"}, {"id": 2002, "name": "Passage de Borlis"}]
        ])

        # Patch GW2Client constructor
        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "uuid" in data
        assert "account_name" in data
        assert "creation_date" in data
        assert "fractal_level" in data
        assert "world_name" in data
        assert "content_access" in data

        # Verify values
        assert data["uuid"] == "12345678-1234-1234-1234-123456789012"
        assert data["account_name"] == "Player.1234"
        assert data["fractal_level"] == 100
        assert isinstance(data["content_access"], list)
        assert len(data["content_access"]) == 4

        # Verify world_name structure
        assert "en" in data["world_name"]
        assert "es" in data["world_name"]
        assert "de" in data["world_name"]
        assert "fr" in data["world_name"]
        assert data["world_name"]["en"] == "Anvil Rock"
        assert data["world_name"]["es"] == "Roca del Yunque"

    async def test_account_details_missing_authorization_header(self):
        """Test that missing authorization header returns 422"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/account/")

        assert response.status_code == 422
        assert "detail" in response.json()

    async def test_account_details_invalid_authorization_format(self):
        """Test that invalid authorization format returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "InvalidFormatWithoutBearer"}
            )

        assert response.status_code == 400
        assert "Invalid authorization header format" in response.json()["detail"]

    async def test_account_details_invalid_authentication_scheme(self):
        """Test that non-Bearer authentication scheme returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Basic sometoken123"}
            )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Invalid" in detail

    async def test_account_details_empty_authorization_header(self):
        """Test that empty authorization header returns 400"""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": ""}
            )

        assert response.status_code == 400
        assert "Invalid authorization header format" in response.json()["detail"]

    async def test_account_details_with_cache(self, mocker: MockerFixture):
        """Test that verifies cache functionality works correctly"""
        mock_account_info = {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "TestPlayer.9999",
            "world": 2003,
            "created": "2015-01-01T00:00:00Z",
            "access": ["GuildWars2"],
            "fractal_level": 50
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            [{"id": 2003, "name": "Yak's Bend"}],
            [{"id": 2003, "name": "Curva del Yak"}],
            [{"id": 2003, "name": "Yakbiegung"}],
            [{"id": 2003, "name": "Courbe du Yak"}]
        ])

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            # First call - should hit the API
            response1 = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer test-cache-key"}
            )
            assert response1.status_code == 200

            # Second call - should use cache
            response2 = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer test-cache-key"}
            )
            assert response2.status_code == 200

            # Verify both responses are equal
            assert response1.json() == response2.json()

            # Client should only have been called once for account info
            assert mock_gw2_client.get_account.call_count == 1

    async def test_account_details_http_401_error(self, mocker: MockerFixture):
        """Test handling of 401 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
        response = httpx.Response(401, request=request, text="Invalid access token")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer invalid-token"}
            )

        assert response.status_code == 401
        assert "Missing or invalid token" in response.json()["detail"]

    async def test_account_details_http_403_error(self, mocker: MockerFixture):
        """Test handling of 403 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
        response = httpx.Response(403, request=request, text="Forbidden")
        error = httpx.HTTPStatusError("Forbidden", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer unauthorized-token"}
            )

        assert response.status_code == 403
        assert "Missing or unauthorized token" in response.json()["detail"]

    async def test_account_details_http_500_error(self, mocker: MockerFixture):
        """Test handling of 500 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
        response = httpx.Response(500, request=request, text="Internal Server Error")
        error = httpx.HTTPStatusError("Server Error", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"

    async def test_account_details_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Connection refused")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 503
        assert "Connection failure" in response.json()["detail"]

    async def test_account_details_generic_error(self, mocker: MockerFixture):
        """Test handling of generic error"""
        error = Exception("Unexpected error")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer some-token"}
            )

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]

    async def test_account_details_world_not_found(self, mocker: MockerFixture):
        """Test handling when world is not found in the worlds list"""
        mock_account_info = {
            "id": "99999999-9999-9999-9999-999999999999",
            "name": "NoWorld.0000",
            "world": 9999,
            "created": "2020-01-01T00:00:00Z",
            "access": ["GuildWars2"],
            "fractal_level": 25
        }

        # World 9999 doesn't exist in the worlds list
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            [{"id": 2001, "name": "Anvil Rock"}],
            [{"id": 2001, "name": "Roca del Yunque"}],
            [{"id": 2001, "name": "Ambossstein"}],
            [{"id": 2001, "name": "Roche de l'Enclume"}]
        ])

        mocker.patch("app.api.v1.account.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/account/",
                headers={"Authorization": "Bearer test-token"}
            )

        assert response.status_code == 200
        data = response.json()

        # Verify that world_name contains None values when world not found
        assert data["world_name"]["en"] is None
        assert data["world_name"]["es"] is None
        assert data["world_name"]["de"] is None
        assert data["world_name"]["fr"] is None


@pytest.mark.asyncio
class TestGetAccountInfoFromApi:
    """Tests for the get_account_info_from_api function"""

    async def test_get_account_info_success(self, mocker: MockerFixture):
        """Test that verifies the function returns account info correctly"""
        mock_account_info = {
            "id": "12345678-1234-1234-1234-123456789012",
            "name": "TestAccount.1234",
            "world": 2001,
            "created": "2013-06-15T12:00:00Z",
            "access": ["GuildWars2", "HeartOfThorns"],
            "fractal_level": 75
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)

        result = await get_account_info_from_api(mock_gw2_client)

        assert result == mock_account_info
        assert result["id"] == "12345678-1234-1234-1234-123456789012"
        assert result["name"] == "TestAccount.1234"
        assert result["world"] == 2001
        assert result["fractal_level"] == 75
        assert len(result["access"]) == 2

    async def test_get_account_info_free_account(self, mocker: MockerFixture):
        """Test with free-to-play account"""
        mock_account_info = {
            "id": "00000000-0000-0000-0000-000000000000",
            "name": "FreePlayer.9999",
            "world": 2005,
            "created": "2022-01-01T00:00:00Z",
            "access": ["PlayForFree"],
            "fractal_level": 0
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)

        result = await get_account_info_from_api(mock_gw2_client)

        assert result["access"] == ["PlayForFree"]
        assert result["fractal_level"] == 0

    async def test_get_account_info_full_expansion_account(self, mocker: MockerFixture):
        """Test with account having all expansions"""
        mock_account_info = {
            "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "name": "VeteranPlayer.0001",
            "world": 2010,
            "created": "2012-08-25T00:00:00Z",
            "access": ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire", "EndOfDragons"],
            "fractal_level": 100
        }

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(return_value=mock_account_info)

        result = await get_account_info_from_api(mock_gw2_client)

        assert len(result["access"]) == 5
        assert "EndOfDragons" in result["access"]
        assert result["fractal_level"] == 100

    async def test_get_account_info_api_error_raises_http_exception(self, mocker: MockerFixture):
        """Test that verifies API errors raise HTTPException"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
        response = httpx.Response(404, request=request, text="Not Found")
        error = httpx.HTTPStatusError("Not Found", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_account_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Not Found"

    async def test_get_account_info_401_error(self, mocker: MockerFixture):
        """Test handling of 401 unauthorized error"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
        response = httpx.Response(401, request=request, text="Invalid access token")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_account_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 401
        assert "Missing or invalid token" in exc.value.detail

    async def test_get_account_info_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Network unreachable")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_account = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_account_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 503
        assert "Connection failure" in exc.value.detail
