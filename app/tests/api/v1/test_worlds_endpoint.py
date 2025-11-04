from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import api
from app.services.dtos.worlds_dto import WorldDTO
from app.services.services import get_worlds_service
from app.services.worlds_service import WorldsService


@pytest.mark.asyncio
class TestWorldsEndpoint:
    """Tests for the /worlds endpoint"""

    async def test_get_worlds_success(self):
        """Test successful response from GET /worlds endpoint"""
        # Arrange - Mock data from service using DTOs
        mock_worlds_data = [
            WorldDTO(
                id=1001,
                name_en="Anvil Rock",
                name_es="Roca del Yunque",
                name_de="Ambossfelsen",
                name_fr="Rocher de l'enclume"
            ),
            WorldDTO(
                id=1002,
                name_en="Borlis Pass",
                name_es="Paso de Borlis",
                name_de="Borlispass",
                name_fr="Passage de Borlis"
            )
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
            side_effect=RuntimeError("No worlds available")
        )

        api.dependency_overrides[get_worlds_service] = lambda: mock_service

        try:
            # Act & Assert - Exception should be raised
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test", follow_redirects=True) as ac:
                with pytest.raises(RuntimeError, match="No worlds available"):
                    await ac.get("/api/v1/worlds")

            # Verify service was called
            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_response_structure(self):
        """Test that response follows the expected WorldsResponse schema"""
        # Arrange
        mock_worlds_data = [
            WorldDTO(
                id=2001,
                name_en="Test World",
                name_es="Mundo de prueba",
                name_de="Testwelt",
                name_fr="Monde de test"
            )
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

            # Verify data types
            assert isinstance(world["id"], int)
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_multiple_worlds(self):
        """Test response with multiple worlds"""
        # Arrange
        mock_worlds_data = [
            WorldDTO(
                id=1000 + i,
                name_en=f"World {i}",
                name_es=f"Mundo {i}",
                name_de=f"Welt {i}",
                name_fr=f"Monde {i}"
            )
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
            WorldDTO(
                id=1001,
                name_en="Anvil Rock",
                name_es="Roca del Yunque",
                name_de="Ambossfelsen",
                name_fr="Rocher de l'enclume"
            )
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
            WorldDTO(
                id=1001,
                name_en="Anvil Rock",
                name_es="Roca del Yunque",
                name_de="Ambossfelsen",
                name_fr="Rocher de l'enclume"
            ),
            WorldDTO(
                id=1002,
                name_en="Borlis Pass",
                name_es="Paso de Borlis",
                name_de="Borlispass",
                name_fr="Passage de Borlis"
            ),
            WorldDTO(
                id=1003,
                name_en="Yak's Bend",
                name_es="Recodo del Yak",
                name_de="Yaks Biegung",
                name_fr="Courbe du yak"
            ),
            WorldDTO(
                id=1004,
                name_en="Henge of Denravi",
                name_es="Círculo de Denravi",
                name_de="Henge von Denravi",
                name_fr="Henge de Denravi"
            ),
            WorldDTO(
                id=1005,
                name_en="Sorrow's Furnace",
                name_es="Horno del Pesar",
                name_de="Sorrows Ofen",
                name_fr="Fourneau du chagrin"
            )
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

            yaks_bend = next(w for w in json_response if w["id"] == 1003)
            assert yaks_bend["name"]["en"] == "Yak's Bend"

            mock_service.get_all_worlds.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_all_languages_present(self):
        """Test that all language translations are present"""
        # Arrange
        mock_worlds_data = [
            WorldDTO(
                id=1001,
                name_en="English Name",
                name_es="Nombre español",
                name_de="Deutscher Name",
                name_fr="Nom français"
            )
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
            assert world["name"]["en"] == "English Name"
            assert world["name"]["es"] == "Nombre español"
            assert world["name"]["de"] == "Deutscher Name"
            assert world["name"]["fr"] == "Nom français"
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_unique_ids(self):
        """Test that world IDs are unique"""
        # Arrange
        mock_worlds_data = [
            WorldDTO(
                id=i,
                name_en=f"World {i}",
                name_es=f"Mundo {i}",
                name_de=f"Welt {i}",
                name_fr=f"Monde {i}"
            )
            for i in [1001, 1002, 1003, 2001, 2002]
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

            # Verify IDs are unique
            ids = [world["id"] for world in json_response]
            assert len(ids) == len(set(ids))  # No duplicates
            assert ids == [1001, 1002, 1003, 2001, 2002]
        finally:
            api.dependency_overrides.clear()

    async def test_get_worlds_single_world(self):
        """Test response with single world"""
        # Arrange
        mock_worlds_data = [
            WorldDTO(
                id=1001,
                name_en="Only World",
                name_es="Único mundo",
                name_de="Einzige Welt",
                name_fr="Seul monde"
            )
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
            assert len(json_response) == 1
            assert json_response[0]["id"] == 1001
            assert json_response[0]["name"]["en"] == "Only World"
        finally:
            api.dependency_overrides.clear()
