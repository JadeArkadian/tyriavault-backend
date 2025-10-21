from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.api.v1.currencies import get_currencies_info_from_api
from app.gw2.client import GW2Client
from app.main import api


@pytest.mark.asyncio
class TestCurrenciesEndpoint:
    """Tests for the /currencies endpoint"""

    async def test_get_currencies_success(self, mocker: MockerFixture):
        """Test successful response from GET /currencies endpoint"""
        # Mock data simulating GW2 API response
        mock_currencies_en = [
            {"id": 1, "name": "Coin", "description": "The primary currency of Tyria", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Earned by helping others", "icon": "https://icon2.png"}
        ]
        mock_currencies_es = [
            {"id": 1, "name": "Moneda", "description": "La moneda principal de Tyria", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Ganado ayudando a otros", "icon": "https://icon2.png"}
        ]
        mock_currencies_de = [
            {"id": 1, "name": "Münze", "description": "Die Hauptwährung von Tyria", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Durch Hilfe für andere verdient", "icon": "https://icon2.png"}
        ]
        mock_currencies_fr = [
            {"id": 1, "name": "Pièce", "description": "La monnaie principale de Tyria", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Gagné en aidant les autres", "icon": "https://icon2.png"}
        ]

        # Mock GW2 client
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currencies_en,
            mock_currencies_es,
            mock_currencies_de,
            mock_currencies_fr
        ])

        # Patch GW2Client constructor
        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify response structure
        assert data[0]["id"] in [1, 2]
        assert "name" in data[0]
        assert "description" in data[0]
        assert "icon_url" in data[0]
        assert "en" in data[0]["name"]
        assert "es" in data[0]["name"]
        assert "de" in data[0]["name"]
        assert "fr" in data[0]["name"]
        assert "en" in data[0]["description"]
        assert "es" in data[0]["description"]
        assert "de" in data[0]["description"]
        assert "fr" in data[0]["description"]

    async def test_get_currencies_with_cache(self, mocker: MockerFixture):
        """Test that verifies cache functionality works correctly"""
        mock_currencies_en = [{"id": 1, "name": "Coin", "description": "Currency", "icon": "https://icon1.png"}]
        mock_currencies_es = [{"id": 1, "name": "Moneda", "description": "Moneda", "icon": "https://icon1.png"}]
        mock_currencies_de = [{"id": 1, "name": "Münze", "description": "Währung", "icon": "https://icon1.png"}]
        mock_currencies_fr = [{"id": 1, "name": "Pièce", "description": "Monnaie", "icon": "https://icon1.png"}]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currencies_en,
            mock_currencies_es,
            mock_currencies_de,
            mock_currencies_fr
        ])

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            # First call - should hit the API
            response1 = await ac.get("/api/v1/currencies/")
            assert response1.status_code == 200

            # Second call - should use cache
            response2 = await ac.get("/api/v1/currencies/")
            assert response2.status_code == 200

            # Verify both responses are equal
            assert response1.json() == response2.json()

            # Client should only have been called once (4 calls for the 4 languages)
            assert mock_gw2_client.get_currencies.call_count == 4

    async def test_get_currencies_http_401_error(self, mocker: MockerFixture):
        """Test handling of 401 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/currencies")
        response = httpx.Response(401, request=request, text="Unauthorized")
        error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 401
        assert "Missing or invalid token" in response.json()["detail"]

    async def test_get_currencies_http_403_error(self, mocker: MockerFixture):
        """Test handling of 403 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/currencies")
        response = httpx.Response(403, request=request, text="Forbidden")
        error = httpx.HTTPStatusError("Forbidden", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 403
        assert "Missing or unauthorized token" in response.json()["detail"]

    async def test_get_currencies_http_500_error(self, mocker: MockerFixture):
        """Test handling of 500 error from GW2 API"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/currencies")
        response = httpx.Response(500, request=request, text="Internal Server Error")
        error = httpx.HTTPStatusError("Server Error", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"

    async def test_get_currencies_connection_error(self, mocker: MockerFixture):
        """Test handling of connection error"""
        error = httpx.ConnectError("Connection refused")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 503
        assert "Connection failure" in response.json()["detail"]

    async def test_get_currencies_generic_error(self, mocker: MockerFixture):
        """Test handling of generic error"""
        error = Exception("Unexpected error")

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        mocker.patch("app.api.v1.currencies.GW2Client", return_value=mock_gw2_client)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/currencies/")

        assert response.status_code == 500
        assert "Internal error" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetCurrenciesInfoFromApi:
    """Tests for the get_currencies_info_from_api function"""

    async def test_get_currencies_info_combines_languages(self, mocker: MockerFixture):
        """Test that verifies the function correctly combines languages"""
        mock_currencies_en = [
            {"id": 1, "name": "Coin", "description": "The primary currency", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Earned by helping", "icon": "https://icon2.png"}
        ]
        mock_currencies_es = [
            {"id": 1, "name": "Moneda", "description": "La moneda principal", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Ganado ayudando", "icon": "https://icon2.png"}
        ]
        mock_currencies_de = [
            {"id": 1, "name": "Münze", "description": "Die Hauptwährung", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Durch Hilfe verdient", "icon": "https://icon2.png"}
        ]
        mock_currencies_fr = [
            {"id": 1, "name": "Pièce", "description": "La monnaie principale", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Gagné en aidant", "icon": "https://icon2.png"}
        ]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currencies_en,
            mock_currencies_es,
            mock_currencies_de,
            mock_currencies_fr
        ])

        result = await get_currencies_info_from_api(mock_gw2_client)

        assert len(result) == 2

        # Verify that all languages were combined
        currency_1 = next(c for c in result if c["id"] == 1)
        assert currency_1["name_en"] == "Coin"
        assert currency_1["name_es"] == "Moneda"
        assert currency_1["name_de"] == "Münze"
        assert currency_1["name_fr"] == "Pièce"
        assert currency_1["description_en"] == "The primary currency"
        assert currency_1["description_es"] == "La moneda principal"
        assert currency_1["description_de"] == "Die Hauptwährung"
        assert currency_1["description_fr"] == "La monnaie principale"
        assert currency_1["icon_url"] == "https://icon1.png"

        currency_2 = next(c for c in result if c["id"] == 2)
        assert currency_2["name_en"] == "Karma"
        assert currency_2["name_es"] == "Karma"
        assert currency_2["name_de"] == "Karma"
        assert currency_2["name_fr"] == "Karma"
        assert currency_2["description_en"] == "Earned by helping"
        assert currency_2["description_es"] == "Ganado ayudando"
        assert currency_2["icon_url"] == "https://icon2.png"

    async def test_get_currencies_info_single_currency(self, mocker: MockerFixture):
        """Test with a single currency"""
        mock_currency_en = [{"id": 1, "name": "Coin", "description": "Currency", "icon": "https://icon1.png"}]
        mock_currency_es = [{"id": 1, "name": "Moneda", "description": "Moneda", "icon": "https://icon1.png"}]
        mock_currency_de = [{"id": 1, "name": "Münze", "description": "Währung", "icon": "https://icon1.png"}]
        mock_currency_fr = [{"id": 1, "name": "Pièce", "description": "Monnaie", "icon": "https://icon1.png"}]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currency_en,
            mock_currency_es,
            mock_currency_de,
            mock_currency_fr
        ])

        result = await get_currencies_info_from_api(mock_gw2_client)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Coin"
        assert result[0]["name_es"] == "Moneda"
        assert result[0]["name_de"] == "Münze"
        assert result[0]["name_fr"] == "Pièce"
        assert result[0]["icon_url"] == "https://icon1.png"

    async def test_get_currencies_info_empty_response(self, mocker: MockerFixture):
        """Test with empty response"""
        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[[], [], [], []])

        result = await get_currencies_info_from_api(mock_gw2_client)

        assert len(result) == 0

    async def test_get_currencies_info_api_error_raises_http_exception(self, mocker: MockerFixture):
        """Test that verifies API errors raise HTTPException"""
        request = httpx.Request("GET", "https://api.guildwars2.com/v2/currencies")
        response = httpx.Response(404, request=request, text="Not Found")
        error = httpx.HTTPStatusError("Not Found", request=request, response=response)

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=error)

        with pytest.raises(HTTPException) as exc:
            await get_currencies_info_from_api(mock_gw2_client)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Not Found"

    async def test_get_currencies_info_multiple_currencies_different_order(self, mocker: MockerFixture):
        """Test that verifies it works even when currencies come in different order"""
        mock_currencies_en = [
            {"id": 1, "name": "Coin", "description": "Currency", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Karma points", "icon": "https://icon2.png"},
            {"id": 3, "name": "Laurel", "description": "Monthly reward", "icon": "https://icon3.png"}
        ]
        mock_currencies_es = [
            {"id": 3, "name": "Laurel", "description": "Recompensa mensual", "icon": "https://icon3.png"},
            {"id": 1, "name": "Moneda", "description": "Moneda", "icon": "https://icon1.png"},
            {"id": 2, "name": "Karma", "description": "Puntos de karma", "icon": "https://icon2.png"}
        ]
        mock_currencies_de = [
            {"id": 2, "name": "Karma", "description": "Karmapunkte", "icon": "https://icon2.png"},
            {"id": 3, "name": "Lorbeer", "description": "Monatliche Belohnung", "icon": "https://icon3.png"},
            {"id": 1, "name": "Münze", "description": "Währung", "icon": "https://icon1.png"}
        ]
        mock_currencies_fr = [
            {"id": 1, "name": "Pièce", "description": "Monnaie", "icon": "https://icon1.png"},
            {"id": 3, "name": "Laurier", "description": "Récompense mensuelle", "icon": "https://icon3.png"},
            {"id": 2, "name": "Karma", "description": "Points de karma", "icon": "https://icon2.png"}
        ]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currencies_en,
            mock_currencies_es,
            mock_currencies_de,
            mock_currencies_fr
        ])

        result = await get_currencies_info_from_api(mock_gw2_client)

        assert len(result) == 3

        # Verify that all currencies have all languages
        for currency_id in [1, 2, 3]:
            currency = next(c for c in result if c["id"] == currency_id)
            assert "name_en" in currency
            assert "name_es" in currency
            assert "name_de" in currency
            assert "name_fr" in currency
            assert "description_en" in currency
            assert "description_es" in currency
            assert "description_de" in currency
            assert "description_fr" in currency
            assert "icon_url" in currency

    async def test_get_currencies_info_icon_url_preserved(self, mocker: MockerFixture):
        """Test that icon URL is correctly preserved from the first language"""
        mock_currencies_en = [{"id": 1, "name": "Coin", "description": "Currency", "icon": "https://render.gw2.png"}]
        mock_currencies_es = [{"id": 1, "name": "Moneda", "description": "Moneda", "icon": "https://render.gw2.png"}]
        mock_currencies_de = [{"id": 1, "name": "Münze", "description": "Währung", "icon": "https://render.gw2.png"}]
        mock_currencies_fr = [{"id": 1, "name": "Pièce", "description": "Monnaie", "icon": "https://render.gw2.png"}]

        mock_gw2_client = mocker.AsyncMock(spec=GW2Client)
        mock_gw2_client.get_currencies = AsyncMock(side_effect=[
            mock_currencies_en,
            mock_currencies_es,
            mock_currencies_de,
            mock_currencies_fr
        ])

        result = await get_currencies_info_from_api(mock_gw2_client)

        assert len(result) == 1
        assert result[0]["icon_url"] == "https://render.gw2.png"
