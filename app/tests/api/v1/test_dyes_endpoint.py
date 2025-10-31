from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import api
from app.services.dyes_service import DyesService
from app.services.services import get_dyes_service


@pytest.mark.asyncio
class TestDyesEndpoint:
    """Tests for the /dyes endpoint"""

    async def test_get_dyes_success(self):
        """Test successful response from GET /dyes endpoint"""
        # Arrange - Mock data from service
        mock_dyes_data = [
            {
                "id": 1,
                "name_en": "Black",
                "name_es": "Negro",
                "name_de": "Schwarz",
                "name_fr": "Noir",
                "color": "#000000"
            },
            {
                "id": 2,
                "name_en": "White",
                "name_es": "Blanco",
                "name_de": "Weiß",
                "name_fr": "Blanc",
                "color": "#ffffff"
            },
            {
                "id": 3,
                "name_en": "Red",
                "name_es": "Rojo",
                "name_de": "Rot",
                "name_fr": "Rouge",
                "color": "#ff0000"
            }
        ]

        # Mock the service
        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        # Override the dependency
        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 3

            # Verify first dye structure
            first_dye = json_response[0]
            assert first_dye["id"] == 1
            assert first_dye["hexcolor"] == "#000000"
            assert "name" in first_dye

            # Verify name translations
            assert first_dye["name"]["en"] == "Black"
            assert first_dye["name"]["es"] == "Negro"
            assert first_dye["name"]["de"] == "Schwarz"
            assert first_dye["name"]["fr"] == "Noir"

            # Verify second dye
            second_dye = json_response[1]
            assert second_dye["id"] == 2
            assert second_dye["name"]["en"] == "White"
            assert second_dye["hexcolor"] == "#ffffff"

            # Verify third dye
            third_dye = json_response[2]
            assert third_dye["id"] == 3
            assert third_dye["name"]["en"] == "Red"
            assert third_dye["hexcolor"] == "#ff0000"

            # Verify service was called
            mock_service.get_all_dyes.assert_called_once()
        finally:
            # Clean up - always clear overrides
            api.dependency_overrides.clear()

    async def test_get_dyes_empty_list(self):
        """Test response when no dyes are available"""
        # Arrange
        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=[])

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            assert response.json() == []
            mock_service.get_all_dyes.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_service_error(self):
        """Test response when service raises an exception"""
        # Arrange
        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(
            side_effect=RuntimeError("No dyes available from API or database")
        )

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act & Assert - Exception should be raised
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test", follow_redirects=True) as ac:
                with pytest.raises(RuntimeError, match="No dyes available from API or database"):
                    await ac.get("/api/v1/dyes")

            # Verify service was called
            mock_service.get_all_dyes.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_response_structure(self):
        """Test that response follows the expected DyesResponse schema"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 123,
                "name_en": "Celestial",
                "name_es": "Celestial",
                "name_de": "Himmlisch",
                "name_fr": "Céleste",
                "color": "#7b2d43"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            dye = json_response[0]

            # Verify required fields exist
            assert "id" in dye
            assert "hexcolor" in dye
            assert "name" in dye

            # Verify name is a dict with all languages
            assert isinstance(dye["name"], dict)
            assert set(dye["name"].keys()) == {"en", "es", "de", "fr"}

            # Verify data types
            assert isinstance(dye["id"], int)
            assert isinstance(dye["hexcolor"], str)

            # Verify hex color format (starts with #)
            assert dye["hexcolor"].startswith("#")
            assert len(dye["hexcolor"]) == 7  # #RRGGBB
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_multiple_dyes(self):
        """Test response with multiple dyes"""
        # Arrange
        mock_dyes_data = [
            {
                "id": i,
                "name_en": f"Dye {i}",
                "name_es": f"Tinte {i}",
                "name_de": f"Farbe {i}",
                "name_fr": f"Teinture {i}",
                "color": f"#{i:06x}"
            }
            for i in range(1, 51)  # 50 dyes
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 50

            # Verify all dyes have correct structure
            for i, dye in enumerate(json_response, start=1):
                assert dye["id"] == i
                assert dye["name"]["en"] == f"Dye {i}"
                assert dye["hexcolor"] == f"#{i:06x}"
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_with_various_colors(self):
        """Test dyes with various hex color values"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 1,
                "name_en": "Black",
                "name_es": "Negro",
                "name_de": "Schwarz",
                "name_fr": "Noir",
                "color": "#000000"
            },
            {
                "id": 2,
                "name_en": "White",
                "name_es": "Blanco",
                "name_de": "Weiß",
                "name_fr": "Blanc",
                "color": "#ffffff"
            },
            {
                "id": 3,
                "name_en": "Gray",
                "name_es": "Gris",
                "name_de": "Grau",
                "name_fr": "Gris",
                "color": "#808080"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify each color
            assert json_response[0]["hexcolor"] == "#000000"
            assert json_response[1]["hexcolor"] == "#ffffff"
            assert json_response[2]["hexcolor"] == "#808080"
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_cache_integration(self):
        """Test that endpoint is configured for caching"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 1,
                "name_en": "Test Dye",
                "name_es": "Tinte de prueba",
                "name_de": "Testfarbe",
                "name_fr": "Teinture test",
                "color": "#123456"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act - Make multiple requests
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response1 = await ac.get("/api/v1/dyes")
                response2 = await ac.get("/api/v1/dyes")

            # Assert - Both should succeed
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Responses should be identical
            assert response1.json() == response2.json()
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_content_type(self):
        """Test that response has correct content type"""
        # Arrange
        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=[])

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_with_primary_colors(self):
        """Test dyes with primary RGB colors"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 1,
                "name_en": "Red",
                "name_es": "Rojo",
                "name_de": "Rot",
                "name_fr": "Rouge",
                "color": "#ff0000"
            },
            {
                "id": 2,
                "name_en": "Green",
                "name_es": "Verde",
                "name_de": "Grün",
                "name_fr": "Vert",
                "color": "#00ff00"
            },
            {
                "id": 3,
                "name_en": "Blue",
                "name_es": "Azul",
                "name_de": "Blau",
                "name_fr": "Bleu",
                "color": "#0000ff"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            assert json_response[0]["name"]["en"] == "Red"
            assert json_response[0]["hexcolor"] == "#ff0000"

            assert json_response[1]["name"]["en"] == "Green"
            assert json_response[1]["hexcolor"] == "#00ff00"

            assert json_response[2]["name"]["en"] == "Blue"
            assert json_response[2]["hexcolor"] == "#0000ff"
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_all_languages_present(self):
        """Test that all language translations are present"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 1,
                "name_en": "English Name",
                "name_es": "Nombre español",
                "name_de": "Deutscher Name",
                "name_fr": "Nom français",
                "color": "#abcdef"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            dye = json_response[0]
            assert dye["name"]["en"] == "English Name"
            assert dye["name"]["es"] == "Nombre español"
            assert dye["name"]["de"] == "Deutscher Name"
            assert dye["name"]["fr"] == "Nom français"
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_unique_ids(self):
        """Test that dye IDs are unique"""
        # Arrange
        mock_dyes_data = [
            {
                "id": i,
                "name_en": f"Dye {i}",
                "name_es": f"Tinte {i}",
                "name_de": f"Farbe {i}",
                "name_fr": f"Teinture {i}",
                "color": f"#{i:06x}"
            }
            for i in [1, 5, 10, 50, 100]
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify IDs are unique
            ids = [dye["id"] for dye in json_response]
            assert len(ids) == len(set(ids))  # No duplicates
            assert ids == [1, 5, 10, 50, 100]
        finally:
            api.dependency_overrides.clear()

    async def test_get_dyes_single_dye(self):
        """Test response with single dye"""
        # Arrange
        mock_dyes_data = [
            {
                "id": 42,
                "name_en": "Only Dye",
                "name_es": "Único tinte",
                "name_de": "Einzige Farbe",
                "name_fr": "Seule teinture",
                "color": "#424242"
            }
        ]

        mock_service = AsyncMock(spec=DyesService)
        mock_service.get_all_dyes = AsyncMock(return_value=mock_dyes_data)

        api.dependency_overrides[get_dyes_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/dyes")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 1
            assert json_response[0]["id"] == 42
            assert json_response[0]["hexcolor"] == "#424242"
        finally:
            api.dependency_overrides.clear()
