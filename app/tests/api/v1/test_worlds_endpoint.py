from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import api
from app.services.services import get_worlds_service
from app.services.worlds_service import WorldsService


@pytest.mark.asyncio
class TestWorldsEndpoint:
    """Tests for the /worlds endpoint"""

    async def test_get_worlds_success(self):
        """Test successful response from GET /worlds endpoint"""
        # Arrange - Mock data from service
        mock_worlds_data = [
            {
                "id": 1001,
                "name_en": "Anvil Rock",
                "name_es": "Roca del Yunque",
                "name_de": "Ambossfelsen",
                "name_fr": "Rocher de l'enclume"
            },
            {
                "id": 1002,
                "name_en": "Borlis Pass",
                "name_es": "Paso de Borlis",
                "name_de": "Borlispass",
                "name_fr": "Passage de Borlis"
            }
        ]

        # Mock the service
        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        # Override the dependency
        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 2

            # Verify first world structure
            first_world = json_response[0]
            assert first_world["id"] == 1001
            assert "name" in first_world

            # Verify name translations
            assert first_world["name"]["en"] == "Anvil Rock"
            assert first_world["name"]["es"] == "Roca del Yunque"
            assert first_world["name"]["de"] == "Ambossfelsen"
            assert first_world["name"]["fr"] == "Rocher de l'enclume"

            # Verify second world
            second_world = json_response[1]
            assert second_world["id"] == 1002
            assert second_world["name"]["en"] == "Borlis Pass"

            # Verify service was called
            mock_service.get_all_worlds.assert_called_once()
        finally:
            # Clean up - always clear overrides
            api.dependency_overrides.clear()

    async def test_get_worlds_empty_list(self):
        """Test response when no worlds are available"""
        # Arrange
        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=[])

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            assert response.json() == []
            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_service_error(self):
        """Test response when service raises an exception"""
        # Arrange
        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(
            side_effect=RuntimeError("No worlds available from API or database")
        )

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act & Assert - Exception should be raised
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test",
                                         follow_redirects=True) as ac:
                with pytest.raises(RuntimeError, match="No worlds available from API or database"):
                    await ac.get("/api/v1/worlds/")

            # Verify service was called
            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_response_structure(self):
        """Test that response follows the expected WorldsResponse schema"""
        # Arrange
        mock_worlds_data = [
            {
                "id": 2001,
                "name_en": "Fissure of Woe",
                "name_es": "Fisura del Infortunio",
                "name_de": "Kluft des Leids",
                "name_fr": "Fissure du malheur"
            }
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            world = json_response[0]

            # Verify required fields exist
            assert "id" in world
            assert "name" in world

            # Verify name is a dict with all languages
            assert isinstance(world["name"], dict)
            assert set(world["name"].keys()) == {"en", "es", "de", "fr"}
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_multiple_worlds(self):
        """Test response with multiple worlds"""
        # Arrange
        mock_worlds_data = [
            {
                "id": 1000 + i,
                "name_en": f"World {i}",
                "name_es": f"Mundo {i}",
                "name_de": f"Welt {i}",
                "name_fr": f"Monde {i}"
            }
            for i in range(1, 51)  # 50 worlds
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 50

            # Verify all worlds have correct structure
            for i, world in enumerate(json_response, start=1):
                assert world["id"] == 1000 + i
                assert world["name"]["en"] == f"World {i}"
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_cache_integration(self):
        """Test that cache is working (service should only be called once for multiple requests)"""
        # Arrange
        mock_worlds_data = [
            {
                "id": 1001,
                "name_en": "Anvil Rock",
                "name_es": "Roca del Yunque",
                "name_de": "Ambossfelsen",
                "name_fr": "Rocher de l'enclume"
            }
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act - Make two requests
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response1 = await ac.get("/api/v1/worlds/")
                response2 = await ac.get("/api/v1/worlds/")

            # Assert
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response1.json() == response2.json()

            # Due to cache, service should only be called once
            assert mock_service.get_all_worlds.call_count == 1
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_content_type(self):
        """Test that response has correct content type"""
        # Arrange
        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=[])

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_real_world_names(self):
        """Test with actual GW2 world names"""
        # Arrange
        mock_worlds_data = [
            {
                "id": 1001,
                "name_en": "Anvil Rock",
                "name_es": "Roca del Yunque",
                "name_de": "Ambossfelsen",
                "name_fr": "Rocher de l'enclume"
            },
            {
                "id": 1002,
                "name_en": "Borlis Pass",
                "name_es": "Paso de Borlis",
                "name_de": "Borlispass",
                "name_fr": "Passage de Borlis"
            },
            {
                "id": 1003,
                "name_en": "Yak's Bend",
                "name_es": "Recodo del Yak",
                "name_de": "Yaks Biegung",
                "name_fr": "Courbe du yak"
            },
            {
                "id": 1004,
                "name_en": "Henge of Denravi",
                "name_es": "Círculo de Denravi",
                "name_de": "Henge von Denravi",
                "name_fr": "Henge de Denravi"
            },
            {
                "id": 1005,
                "name_en": "Sorrow's Furnace",
                "name_es": "Horno del Pesar",
                "name_de": "Sorrows Ofen",
                "name_fr": "Fourneau du chagrin"
            }
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 5

            # Verify specific worlds
            anvil_rock = next(w for w in json_response if w["id"] == 1001)
            assert anvil_rock["name"]["en"] == "Anvil Rock"
            assert anvil_rock["name"]["es"] == "Roca del Yunque"

            sorrows_furnace = next(w for w in json_response if w["id"] == 1005)
            assert sorrows_furnace["name"]["en"] == "Sorrow's Furnace"
            assert sorrows_furnace["name"]["fr"] == "Fourneau du chagrin"

            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_all_languages_present(self):
        """Test that all language keys are present in the response"""
        # Arrange
        mock_worlds_data = [
            {
                "id": 2001,
                "name_en": "Test World EN",
                "name_es": "Test World ES",
                "name_de": "Test World DE",
                "name_fr": "Test World FR"
            }
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            world = json_response[0]

            # Verify all languages are present
            assert "en" in world["name"]
            assert "es" in world["name"]
            assert "de" in world["name"]
            assert "fr" in world["name"]

            # Verify correct values
            assert world["name"]["en"] == "Test World EN"
            assert world["name"]["es"] == "Test World ES"
            assert world["name"]["de"] == "Test World DE"
            assert world["name"]["fr"] == "Test World FR"
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_unique_ids(self):
        """Test that all worlds have unique IDs"""
        # Arrange
        mock_worlds_data = [
            {
                "id": id_num,
                "name_en": f"World {id_num}",
                "name_es": f"Mundo {id_num}",
                "name_de": f"Welt {id_num}",
                "name_fr": f"Monde {id_num}"
            }
            for id_num in [1001, 1002, 1003, 1004, 1005]
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds/")

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Extract all IDs
            ids = [world["id"] for world in json_response]

            # Verify all IDs are unique
            assert len(ids) == len(set(ids))
            assert set(ids) == {1001, 1002, 1003, 1004, 1005}
        finally:
            api.dependency_overrides.clear()
