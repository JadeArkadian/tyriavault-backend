from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.models import Worlds
from app.services.worlds_service import WorldsService


@pytest.fixture
def mock_repository():
    """Mock of the worlds repository"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock of the GW2 client"""
    client = AsyncMock()
    return client


@pytest.fixture
def worlds_service(mock_repository, mock_gw2_client):
    """Fixture for the worlds service"""
    return WorldsService(repository=mock_repository, gw2_client=mock_gw2_client)


@pytest.fixture
def sample_api_response_en():
    """Sample GW2 API response in English"""
    return [
        {
            "id": 1001,
            "name": "Anvil Rock",
            "population": "High"
        },
        {
            "id": 1002,
            "name": "Borlis Pass",
            "population": "Medium"
        }
    ]


@pytest.fixture
def sample_api_response_es():
    """Sample GW2 API response in Spanish"""
    return [
        {
            "id": 1001,
            "name": "Roca del Yunque",
            "population": "High"
        },
        {
            "id": 1002,
            "name": "Paso de Borlis",
            "population": "Medium"
        }
    ]


@pytest.fixture
def sample_api_response_de():
    """Sample GW2 API response in German"""
    return [
        {
            "id": 1001,
            "name": "Ambossfelsen",
            "population": "High"
        },
        {
            "id": 1002,
            "name": "Borlispass",
            "population": "Medium"
        }
    ]


@pytest.fixture
def sample_api_response_fr():
    """Sample GW2 API response in French"""
    return [
        {
            "id": 1001,
            "name": "Rocher de l'enclume",
            "population": "High"
        },
        {
            "id": 1002,
            "name": "Passage de Borlis",
            "population": "Medium"
        }
    ]


@pytest.fixture
def sample_db_worlds():
    """Sample worlds from the database"""
    world1 = MagicMock(spec=Worlds)
    world1.id = 1001
    world1.name_en = "Anvil Rock"
    world1.name_es = "Roca del Yunque"
    world1.name_de = "Ambossfelsen"
    world1.name_fr = "Rocher de l'enclume"

    world2 = MagicMock(spec=Worlds)
    world2.id = 1002
    world2.name_en = "Borlis Pass"
    world2.name_es = "Paso de Borlis"
    world2.name_de = "Borlispass"
    world2.name_fr = "Passage de Borlis"

    return [world1, world2]


class TestWorldsService:
    """Test suite for WorldsService"""

    @pytest.mark.asyncio
    async def test_get_all_worlds_success_from_db(
            self,
            worlds_service,
            mock_repository,
            sample_db_worlds
    ):
        """Test: successfully get worlds from the database"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_worlds

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["name_en"] == "Anvil Rock"
        assert result[0]["name_es"] == "Roca del Yunque"
        assert result[0]["name_de"] == "Ambossfelsen"
        assert result[0]["name_fr"] == "Rocher de l'enclume"
        assert result[1]["id"] == 1002
        assert result[1]["name_en"] == "Borlis Pass"

        # Verify that only the repository was called
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_worlds_fallback_to_api_when_db_empty(
            self,
            worlds_service,
            mock_repository,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: get worlds from API when DB is empty"""
        # Arrange
        mock_repository.get_all.side_effect = ValueError("No worlds found in database")
        mock_gw2_client.get_worlds.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["name_en"] == "Anvil Rock"
        assert result[0]["name_es"] == "Roca del Yunque"
        assert result[0]["name_de"] == "Ambossfelsen"
        assert result[0]["name_fr"] == "Rocher de l'enclume"

        # Verify that DB was tried first
        mock_repository.get_all.assert_called_once()

        # Verify that API was called for all languages
        assert mock_gw2_client.get_worlds.call_count == 4

    @pytest.mark.asyncio
    async def test_get_all_worlds_fallback_to_api_when_db_fails(
            self,
            worlds_service,
            mock_repository,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: get worlds from API when DB fails"""
        # Arrange
        mock_repository.get_all.side_effect = Exception("Database connection error")
        mock_gw2_client.get_worlds.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1001
        mock_repository.get_all.assert_called_once()
        assert mock_gw2_client.get_worlds.call_count == 4

    @pytest.mark.asyncio
    async def test_get_worlds_from_api_combines_all_languages(
            self,
            worlds_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: _get_worlds_from_api correctly combines all languages"""
        # Arrange
        mock_gw2_client.get_worlds.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await worlds_service._get_worlds_from_api()

        # Assert
        assert len(result) == 2

        # Verify first world
        world_1001 = next(w for w in result if w["id"] == 1001)
        assert world_1001["name_en"] == "Anvil Rock"
        assert world_1001["name_es"] == "Roca del Yunque"
        assert world_1001["name_de"] == "Ambossfelsen"
        assert world_1001["name_fr"] == "Rocher de l'enclume"

        # Verify second world
        world_1002 = next(w for w in result if w["id"] == 1002)
        assert world_1002["name_en"] == "Borlis Pass"
        assert world_1002["name_es"] == "Paso de Borlis"
        assert world_1002["name_de"] == "Borlispass"
        assert world_1002["name_fr"] == "Passage de Borlis"

        # Verify that API was called for each language
        assert mock_gw2_client.get_worlds.call_count == 4
        calls = mock_gw2_client.get_worlds.call_args_list
        assert calls[0].kwargs["lang"] == "en"
        assert calls[1].kwargs["lang"] == "es"
        assert calls[2].kwargs["lang"] == "de"
        assert calls[3].kwargs["lang"] == "fr"

    @pytest.mark.asyncio
    async def test_get_worlds_from_db_success(
            self,
            worlds_service,
            mock_repository,
            sample_db_worlds
    ):
        """Test: _get_worlds_from_db correctly returns data"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_worlds

        # Act
        result = await worlds_service._get_worlds_from_db()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1001
        assert result[0]["name_en"] == "Anvil Rock"
        assert result[1]["id"] == 1002
        assert result[1]["name_en"] == "Borlis Pass"
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_worlds_from_db_raises_when_empty(
            self,
            worlds_service,
            mock_repository
    ):
        """Test: _get_worlds_from_db raises exception when no data exists"""
        # Arrange
        mock_repository.get_all.return_value = []

        # Act & Assert
        with pytest.raises(ValueError, match="No worlds found in database"):
            await worlds_service._get_worlds_from_db()

    @pytest.mark.asyncio
    async def test_get_worlds_from_db_raises_when_repository_fails(
            self,
            worlds_service,
            mock_repository
    ):
        """Test: _get_worlds_from_db propagates repository exceptions"""
        # Arrange
        mock_repository.get_all.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await worlds_service._get_worlds_from_db()

    @pytest.mark.asyncio
    async def test_sync_worlds_to_db_success(
            self,
            worlds_service,
            mock_repository
    ):
        """Test: _sync_worlds_to_db correctly synchronizes data"""
        # Arrange
        worlds_data = [
            {
                "id": 1001,
                "name_en": "Anvil Rock",
                "name_es": "Roca del Yunque",
                "name_de": "Ambossfelsen",
                "name_fr": "Rocher de l'enclume"
            }
        ]

        # Mock async_session_maker
        mock_session = AsyncMock()
        mock_new_repository = AsyncMock()

        with patch('app.services.worlds_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.worlds_service.WorldsRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_new_repository

                # Act
                await worlds_service._sync_worlds_to_db(worlds_data)

                # Assert
                mock_new_repository.upsert_batch.assert_called_once_with(worlds_data)

    @pytest.mark.asyncio
    async def test_sync_worlds_to_db_handles_errors(
            self,
            worlds_service
    ):
        """Test: _sync_worlds_to_db handles errors without propagating exception"""
        # Arrange
        worlds_data = [{"id": 1001, "name_en": "Test"}]

        with patch('app.services.worlds_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB error")

            # Act (should not raise exception)
            await worlds_service._sync_worlds_to_db(worlds_data)

            # Assert - function should handle error without propagating it
            assert True  # If we reach here, exception was not propagated

    @pytest.mark.asyncio
    async def test_get_all_worlds_creates_background_task_on_api_fallback(
            self,
            worlds_service,
            mock_repository,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: background task is created to sync with DB when API is used"""
        # Arrange
        mock_repository.get_all.side_effect = ValueError("No worlds found in database")
        mock_gw2_client.get_worlds.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert worlds_service.task is not None
        assert not worlds_service.task.done() or worlds_service.task.done()
        # Verify that task was created, regardless of whether it's finished

    @pytest.mark.asyncio
    async def test_get_all_worlds_no_background_task_when_db_success(
            self,
            worlds_service,
            mock_repository,
            sample_db_worlds
    ):
        """Test: no background task is created when DB returns data successfully"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_worlds
        worlds_service.task = None

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert worlds_service.task is None
