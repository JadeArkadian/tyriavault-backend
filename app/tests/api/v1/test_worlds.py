from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.api.v1.worlds import get_worlds_info_from_api
from app.gw2.client import GW2Client
from app.main import api


@pytest.mark.asyncio
class TestWorldsEndpoint:
    """Tests for the /worlds endpoint"""

    async def test_get_worlds_success(self, mocker: MockerFixture):
        """Test successful response from GET /worlds endpoint"""
        # Mock data simulating GW2 API response
        mock_worlds_en = [
            {"id": 1001, "name": "Anvil Rock", "population": "Medium"},
            {"id": 1002, "name": "Borlis Pass", "population": "High"}
        ]
        mock_worlds_es = [
            {"id": 1001, "name": "Roca del Yunque", "population": "Medium"},
            {"id": 1002, "name": "Paso de Borlis", "population": "High"}
        ]
        mock_worlds_de = [
            {"id": 1001, "name": "Ambossstein", "population": "Medium"},
            {"id": 1002, "name": "Borlispass", "population": "High"}
        ]
        mock_worlds_fr = [
            {"id": 1001, "name": "Roche de l'Enclume", "population": "Medium"},
            {"id": 1002, "name": "Passage de Borlis", "population": "High"}
        ]

        # Mock GW2 client
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            mock_worlds_en,
            mock_worlds_es,
            mock_worlds_de,
            mock_worlds_fr
        ])

        # Patch GW2Client constructor
        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify response structure
        assert data[0]["id"] in [1001, 1002]
        assert "name" in data[0]
        assert "en" in data[0]["name"]
        assert "es" in data[0]["name"]
        assert "de" in data[0]["name"]
        assert "fr" in data[0]["name"]

    async def test_get_worlds_with_cache(self, mocker: MockerFixture):
        """Test that verifies cache functionality works correctly"""
        mock_worlds_en = [{"id": 1001, "name": "Anvil Rock"}]
        mock_worlds_es = [{"id": 1001, "name": "Roca del Yunque"}]
        mock_worlds_de = [{"id": 1001, "name": "Ambossstein"}]
        mock_worlds_fr = [{"id": 1001, "name": "Roche de l'Enclume"}]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            mock_worlds_en,
            mock_worlds_es,
            mock_worlds_de,
            mock_worlds_fr
        ])

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            # First call - should hit the API
            response1 = await ac.get("/api/v1/worlds/")
            assert response1.status_code == 200

            # Second call - should use cache
            response2 = await ac.get("/api/v1/worlds/")
            assert response2.status_code == 200

            # Verify both responses are equal
            assert response1.json() == response2.json()

            # Client should only have been called once (4 calls for the 4 languages)
            assert mock_gw2_client.get_worlds.call_count == 4

    async def test_get_worlds_http_401_error(self, mocker: MockerFixture):
        """Test handling of 401 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/worlds")
        response = httpx.Response(401, request=request, text="Unauthorized")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 401
        assert "Missing or invalid token" in response.json()["detail"]

    async def test_get_worlds_http_403_error(self, mocker: MockerFixture):
        """Test handling of 403 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/worlds")
        response = httpx.Response(403, request=request, text="Forbidden")
        error = httpx.HTTPStatusError("Forbidden", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 403
        assert "Missing or unauthorized token" in response.json()["detail"]

    async def test_get_worlds_http_500_error(self, mocker: MockerFixture):
        """Test handling of 500 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/worlds")
        response = httpx.Response(500, request=request, text="Internal Server Error")
        error = httpx.HTTPStatusError("Server Error", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"

    async def test_get_worlds_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Connection refused")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 503
        assert "Connection failure" in response.json()["detail"]

    async def test_get_worlds_generic_error(self, mocker: MockerFixture):
        """Test handling of generic error"""
        error = Exception("Unexpected error")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.worlds.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/worlds/")

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetWorldsInfoFromApi:
    """Tests for the get_worlds_info_from_api function"""

    async def test_get_worlds_info_combines_languages(self, mocker: MockerFixture):
        """Test that verifies the function correctly combines languages"""
        mock_worlds_en = [
            {"id": 1001, "name": "Anvil Rock"},
            {"id": 1002, "name": "Borlis Pass"}
        ]
        mock_worlds_es = [
            {"id": 1001, "name": "Roca del Yunque"},
            {"id": 1002, "name": "Paso de Borlis"}
        ]
        mock_worlds_de = [
            {"id": 1001, "name": "Ambossstein"},
            {"id": 1002, "name": "Borlispass"}
        ]
        mock_worlds_fr = [
            {"id": 1001, "name": "Roche de l'Enclume"},
            {"id": 1002, "name": "Passage de Borlis"}
        ]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            mock_worlds_en,
            mock_worlds_es,
            mock_worlds_de,
            mock_worlds_fr
        ])

        result = await get_worlds_info_from_api(mock_gw2_client)

        assert len(result) == 2

        # Verify that all languages were combined
        world_1001 = next(w for w in result if w["id"] == 1001)
        assert world_1001["name_en"] == "Anvil Rock"
        assert world_1001["name_es"] == "Roca del Yunque"
        assert world_1001["name_de"] == "Ambossstein"
        assert world_1001["name_fr"] == "Roche de l'Enclume"

        world_1002 = next(w for w in result if w["id"] == 1002)
        assert world_1002["name_en"] == "Borlis Pass"
        assert world_1002["name_es"] == "Paso de Borlis"
        assert world_1002["name_de"] == "Borlispass"
        assert world_1002["name_fr"] == "Passage de Borlis"

    async def test_get_worlds_info_single_world(self, mocker: MockerFixture):
        """Test with a single world"""
        mock_world_en = [{"id": 1001, "name": "Anvil Rock"}]
        mock_world_es = [{"id": 1001, "name": "Roca del Yunque"}]
        mock_world_de = [{"id": 1001, "name": "Ambossstein"}]
        mock_world_fr = [{"id": 1001, "name": "Roche de l'Enclume"}]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            mock_world_en,
            mock_world_es,
            mock_world_de,
            mock_world_fr
        ])

        result = await get_worlds_info_from_api(mock_gw2_client)

        assert len(result) == 1
        assert result[0]["id"] == 1001
        assert result[0]["name_en"] == "Anvil Rock"
        assert result[0]["name_es"] == "Roca del Yunque"
        assert result[0]["name_de"] == "Ambossstein"
        assert result[0]["name_fr"] == "Roche de l'Enclume"

    async def test_get_worlds_info_empty_response(self, mocker: MockerFixture):
        """Test with empty response"""
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[[], [], [], []])

        result = await get_worlds_info_from_api(mock_gw2_client)

        assert len(result) == 0

    async def test_get_worlds_info_api_error_raises_http_exception(self, mocker: MockerFixture):
        """Test that verifies API errors raise HTTPException"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/worlds")
        response = httpx.Response(404, request=request, text="Not Found")
        error = httpx.HTTPStatusError("Not Found", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_worlds_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Not Found"

    async def test_get_worlds_info_multiple_worlds_different_order(self, mocker: MockerFixture):
        """Test that verifies it works even when worlds come in different order"""
        mock_worlds_en = [
            {"id": 1001, "name": "Anvil Rock"},
            {"id": 1002, "name": "Borlis Pass"},
            {"id": 1003, "name": "Crystal Desert"}
        ]
        mock_worlds_es = [
            {"id": 1003, "name": "Desierto de Cristal"},
            {"id": 1001, "name": "Roca del Yunque"},
            {"id": 1002, "name": "Paso de Borlis"}
        ]
        mock_worlds_de = [
            {"id": 1002, "name": "Borlispass"},
            {"id": 1003, "name": "Kristallwüste"},
            {"id": 1001, "name": "Ambossstein"}
        ]
        mock_worlds_fr = [
            {"id": 1001, "name": "Roche de l'Enclume"},
            {"id": 1003, "name": "Désert de Cristal"},
            {"id": 1002, "name": "Passage de Borlis"}
        ]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_worlds = AsyncMock(side_effect=[
            mock_worlds_en,
            mock_worlds_es,
            mock_worlds_de,
            mock_worlds_fr
        ])

        result = await get_worlds_info_from_api(mock_gw2_client)

        assert len(result) == 3

        # Verify that all worlds have all languages
        for world_id in [1001, 1002, 1003]:
            world = next(w for w in result if w["id"] == world_id)
            assert "name_en" in world
            assert "name_es" in world
            assert "name_de" in world
            assert "name_fr" in world
