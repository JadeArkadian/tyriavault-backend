from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.database.models import Worlds
from app.main import api
from app.services.services import get_worlds_service
from app.services.worlds_service import WorldsService


def create_mock_world(world_id: int, name_en: str, name_es: str, name_de: str, name_fr: str) -> MagicMock:
    """Helper function to create a mock Worlds object"""
    world = MagicMock(spec=Worlds)
    world.id = world_id
    world.name_en = name_en
    world.name_es = name_es
    world.name_de = name_de
    world.name_fr = name_fr
    return world


@pytest.mark.asyncio
class TestWorldsEndpoint:
    """Tests for the /worlds endpoint"""

    async def test_get_worlds_success(self):
        """Test successful response from GET /worlds endpoint"""
        # Arrange - Mock data from service
        mock_worlds_data = [
            create_mock_world(1001, "Anvil Rock", "Roca del Yunque", "Ambossfelsen", "Rocher de l'enclume"),
            create_mock_world(1002, "Borlis Pass", "Paso de Borlis", "Borlispass", "Passage de Borlis")
        ]

        # Mock the service
        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        # Override the dependency
        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
                response = await ac.get("/api/v1/worlds")

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
                    await ac.get("/api/v1/worlds")

            # Verify service was called
            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_response_structure(self):
        """Test that response follows the expected WorldsResponse schema"""
        # Arrange
        mock_worlds_data = [
            create_mock_world(2001, "Fissure of Woe", "Fisura del Infortunio", "Kluft des Leids", "Fissure du malheur")
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
            create_mock_world(1000 + i, f"World {i}", f"Mundo {i}", f"Welt {i}", f"Monde {i}")
            for i in range(1, 51)  # 50 worlds
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
            create_mock_world(1001, "Anvil Rock", "Roca del Yunque", "Ambossfelsen", "Rocher de l'enclume")
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act - Make two requests
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response1 = await ac.get("/api/v1/worlds")
                response2 = await ac.get("/api/v1/worlds")

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
                response = await ac.get("/api/v1/worlds")

            # Assert
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_real_world_names(self):
        """Test with actual GW2 world names"""
        # Arrange
        mock_worlds_data = [
            create_mock_world(1001, "Anvil Rock", "Roca del Yunque", "Ambossfelsen", "Rocher de l'enclume"),
            create_mock_world(1002, "Borlis Pass", "Paso de Borlis", "Borlispass", "Passage de Borlis"),
            create_mock_world(1003, "Yak's Bend", "Recodo del Yak", "Yaks Biegung", "Courbe du yak"),
            create_mock_world(1004, "Henge of Denravi", "Círculo de Denravi", "Henge von Denravi", "Henge de Denravi"),
            create_mock_world(1005, "Sorrow's Furnace", "Horno del Pesar", "Sorrows Ofen", "Fourneau du chagrin")
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
            create_mock_world(2001, "Test World EN", "Test World ES", "Test World DE", "Test World FR")
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
            create_mock_world(id_num, f"World {id_num}", f"Mundo {id_num}", f"Welt {id_num}", f"Monde {id_num}")
            for id_num in [1001, 1002, 1003, 1004, 1005]
        ]

        mock_service = AsyncMock(spec=WorldsService)
        mock_service.get_all_worlds = AsyncMock(return_value=mock_worlds_data)

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get("/api/v1/worlds")

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
