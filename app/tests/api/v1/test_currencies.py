from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import api
from app.services.currencies_service import CurrenciesService
from app.services.services import get_currencies_service


@pytest.mark.asyncio
class TestCurrenciesEndpoint:
    """Tests for the /currencies endpoint"""

    async def test_get_currencies_success(self):
        """Test successful response from GET /currencies endpoint"""
        # Arrange - Mock data from service
        mock_currencies_data = [
            {
                "id": 1,
                "name_en": "Coin",
                "name_es": "Moneda",
                "name_de": "Münze",
                "name_fr": "Pièce",
                "description_en": "The primary currency",
                "description_es": "La moneda principal",
                "description_de": "Die Hauptwährung",
                "description_fr": "La monnaie principale",
                "icon_url": "https://render.guildwars2.com/file/coin.png"
            },
            {
                "id": 2,
                "name_en": "Karma",
                "name_es": "Karma",
                "name_de": "Karma",
                "name_fr": "Karma",
                "description_en": "Earned by helping others",
                "description_es": "Ganado ayudando a otros",
                "description_de": "Verdient durch Hilfe für andere",
                "description_fr": "Gagné en aidant les autres",
                "icon_url": "https://render.guildwars2.com/file/karma.png"
            }
        ]

        # Mock the service
        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=mock_currencies_data)

        # Override the dependency
        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 2

            # Verify first currency structure
            first_currency = json_response[0]
            assert first_currency["id"] == 1
            assert first_currency["icon_url"] == "https://render.guildwars2.com/file/coin.png"
            assert "name" in first_currency
            assert "description" in first_currency

            # Verify name translations
            assert first_currency["name"]["en"] == "Coin"
            assert first_currency["name"]["es"] == "Moneda"
            assert first_currency["name"]["de"] == "Münze"
            assert first_currency["name"]["fr"] == "Pièce"

            # Verify description translations
            assert first_currency["description"]["en"] == "The primary currency"
            assert first_currency["description"]["es"] == "La moneda principal"

            # Verify second currency
            second_currency = json_response[1]
            assert second_currency["id"] == 2
            assert second_currency["name"]["en"] == "Karma"

            # Verify service was called
            mock_service.get_all_currencies.assert_called_once()
        finally:
            # Clean up - always clear overrides
            api.dependency_overrides.clear()

    async def test_get_currencies_empty_list(self):
        """Test response when no currencies are available"""
        # Arrange
        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=[])

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            assert response.json() == []
            mock_service.get_all_currencies.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_service_error(self):
        """Test response when service raises an exception"""
        # Arrange
        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(
            side_effect=RuntimeError("No currencies available from API or database")
        )

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act & Assert - Exception should be raised
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test", follow_redirects=True) as ac:
                with pytest.raises(RuntimeError, match="No currencies available from API or database"):
                    await ac.get("/api/v1/currencies/")

            # Verify service was called
            mock_service.get_all_currencies.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_response_structure(self):
        """Test that response follows the expected CurrenciesResponse schema"""
        # Arrange
        mock_currencies_data = [
            {
                "id": 23,
                "name_en": "Laurels",
                "name_es": "Laureles",
                "name_de": "Lorbeeren",
                "name_fr": "Lauriers",
                "description_en": "Earned for daily login rewards",
                "description_es": "Obtenidos por recompensas de inicio de sesión diarias",
                "description_de": "Verdient für tägliche Anmeldebelohnungen",
                "description_fr": "Gagné pour les récompenses de connexion quotidiennes",
                "icon_url": "https://render.guildwars2.com/file/laurel.png"
            }
        ]

        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=mock_currencies_data)

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            currency = json_response[0]

            # Verify required fields exist
            assert "id" in currency
            assert "icon_url" in currency
            assert "name" in currency
            assert "description" in currency

            # Verify name is a dict with all languages
            assert isinstance(currency["name"], dict)
            assert set(currency["name"].keys()) == {"en", "es", "de", "fr"}

            # Verify description is a dict with all languages
            assert isinstance(currency["description"], dict)
            assert set(currency["description"].keys()) == {"en", "es", "de", "fr"}
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_with_null_icon(self):
        """Test response when icon_url is None"""
        # Arrange
        mock_currencies_data = [
            {
                "id": 99,
                "name_en": "Test Currency",
                "name_es": "Moneda de prueba",
                "name_de": "Testwährung",
                "name_fr": "Monnaie de test",
                "description_en": "Test description",
                "description_es": "Descripción de prueba",
                "description_de": "Testbeschreibung",
                "description_fr": "Description de test",
                "icon_url": None
            }
        ]

        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=mock_currencies_data)

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert json_response[0]["icon_url"] is None
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_multiple_currencies(self):
        """Test response with multiple currencies"""
        # Arrange
        mock_currencies_data = [
            {
                "id": i,
                "name_en": f"Currency {i}",
                "name_es": f"Moneda {i}",
                "name_de": f"Währung {i}",
                "name_fr": f"Monnaie {i}",
                "description_en": f"Description {i}",
                "description_es": f"Descripción {i}",
                "description_de": f"Beschreibung {i}",
                "description_fr": f"Description {i}",
                "icon_url": f"https://example.com/icon{i}.png"
            }
            for i in range(1, 51)  # 50 currencies
        ]

        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=mock_currencies_data)

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 50

            # Verify all currencies have correct structure
            for i, currency in enumerate(json_response, start=1):
                assert currency["id"] == i
                assert currency["name"]["en"] == f"Currency {i}"
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_cache_integration(self):
        """Test that cache is working (service should only be called once for multiple requests)"""
        # Arrange
        mock_currencies_data = [
            {
                "id": 1,
                "name_en": "Coin",
                "name_es": "Moneda",
                "name_de": "Münze",
                "name_fr": "Pièce",
                "description_en": "The primary currency",
                "description_es": "La moneda principal",
                "description_de": "Die Hauptwährung",
                "description_fr": "La monnaie principale",
                "icon_url": "https://render.guildwars2.com/file/coin.png"
            }
        ]

        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=mock_currencies_data)

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act - Make two requests
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response1 = await ac.get("/api/v1/currencies/")
                response2 = await ac.get("/api/v1/currencies/")

            # Assert
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response1.json() == response2.json()

            # Due to cache, service should only be called once
            assert mock_service.get_all_currencies.call_count == 1
        finally:
            api.dependency_overrides.clear()

    async def test_get_currencies_content_type(self):
        """Test that response has correct content type"""
        # Arrange
        mock_service = AsyncMock(spec=CurrenciesService)
        mock_service.get_all_currencies = AsyncMock(return_value=[])

        api.dependency_overrides[get_currencies_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/currencies/")

            # Assert
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
        finally:
            api.dependency_overrides.clear()
