from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.models import Worlds
from app.gw2.responses import GW2ApiWorld
from app.services.dtos.worlds_dto import WorldDTO
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
        GW2ApiWorld(id=1001, name="Anvil Rock", population="High"),
        GW2ApiWorld(id=1002, name="Borlis Pass", population="Medium")
    ]


@pytest.fixture
def sample_api_response_es():
    """Sample GW2 API response in Spanish"""
    return [
        GW2ApiWorld(id=1001, name="Roca del Yunque", population="High"),
        GW2ApiWorld(id=1002, name="Paso de Borlis", population="Medium")
    ]


@pytest.fixture
def sample_api_response_de():
    """Sample GW2 API response in German"""
    return [
        GW2ApiWorld(id=1001, name="Ambossfelsen", population="High"),
        GW2ApiWorld(id=1002, name="Borlispass", population="Medium")
    ]


@pytest.fixture
def sample_api_response_fr():
    """Sample GW2 API response in French"""
    return [
        GW2ApiWorld(id=1001, name="Rocher de l'enclume", population="High"),
        GW2ApiWorld(id=1002, name="Passage de Borlis", population="Medium")
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
    async def test_get_all_worlds_success_from_api(
            self,
            worlds_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: successfully get worlds from API (new circuit breaker strategy: API first)"""
        # Arrange
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
        assert isinstance(result[0], WorldDTO)
        assert result[0].id == 1001
        assert result[0].name_en == "Anvil Rock"
        assert result[0].name_es == "Roca del Yunque"
        assert result[0].name_de == "Ambossfelsen"
        assert result[0].name_fr == "Rocher de l'enclume"
        assert isinstance(result[1], WorldDTO)
        assert result[1].id == 1002
        assert result[1].name_en == "Borlis Pass"

        # Verify that API was called for all languages
        assert mock_gw2_client.get_worlds.call_count == 4

    @pytest.mark.asyncio
    async def test_get_all_worlds_fallback_to_db_when_api_fails(
            self,
            worlds_service,
            mock_repository,
            mock_gw2_client,
            sample_db_worlds
    ):
        """Test: get worlds from DB when API fails (circuit breaker protection)"""
        from app.gw2.gw2_client import GW2ApiError

        # Arrange - API fails with GW2ApiError (circuit breaker open or timeout)
        mock_gw2_client.get_worlds.side_effect = GW2ApiError("Circuit breaker open: API is unavailable")
        mock_repository.get_all.return_value = sample_db_worlds

        # Act
        result = await worlds_service.get_all_worlds()

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], WorldDTO)
        assert result[0].id == 1001
        assert result[0].name_en == "Anvil Rock"

        # Verify that API was tried (for first language before falling back)
        assert mock_gw2_client.get_worlds.call_count >= 1
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_worlds_raises_when_both_fail(
            self,
            worlds_service,
            mock_repository,
            mock_gw2_client
    ):
        """Test: raises error when both API and DB fail"""
        from app.gw2.gw2_client import GW2ApiError

        # Arrange - Both API and DB fail
        mock_gw2_client.get_worlds.side_effect = GW2ApiError("Circuit breaker open")
        mock_repository.get_all.side_effect = Exception("Database connection error")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc:
            await worlds_service.get_all_worlds()

        assert "Both API and database failed" in str(exc.value)

        # Verify both were attempted
        assert mock_gw2_client.get_worlds.call_count >= 1
        mock_repository.get_all.assert_called_once()

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
        world_1001 = next(w for w in result if w.id == 1001)
        assert isinstance(world_1001, WorldDTO)
        assert world_1001.name_en == "Anvil Rock"
        assert world_1001.name_es == "Roca del Yunque"
        assert world_1001.name_de == "Ambossfelsen"
        assert world_1001.name_fr == "Rocher de l'enclume"

        # Verify second world
        world_1002 = next(w for w in result if w.id == 1002)
        assert isinstance(world_1002, WorldDTO)
        assert world_1002.name_en == "Borlis Pass"
        assert world_1002.name_es == "Paso de Borlis"
        assert world_1002.name_de == "Borlispass"
        assert world_1002.name_fr == "Passage de Borlis"

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
        assert isinstance(result[0], WorldDTO)
        assert result[0].id == 1001
        assert result[0].name_en == "Anvil Rock"
        assert isinstance(result[1], WorldDTO)
        assert result[1].id == 1002
        assert result[1].name_en == "Borlis Pass"
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
            worlds_service
    ):
        """Test: _sync_worlds_to_db correctly synchronizes data"""
        # Arrange
        worlds_data = [
            WorldDTO(
                id=1001,
                name_en="Anvil Rock",
                name_es="Roca del Yunque",
                name_de="Ambossfelsen",
                name_fr="Rocher de l'enclume"
            )
        ]

        mock_session = AsyncMock()
        mock_new_repository = AsyncMock()

        with patch('app.services.worlds_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.worlds_service.WorldsRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_new_repository

                # Act
                await worlds_service._sync_worlds_to_db(worlds_data)

                # Assert - DTOs should be converted to ORM objects
                assert mock_new_repository.upsert_batch.call_count == 1
                call_args = mock_new_repository.upsert_batch.call_args[0][0]
                assert len(call_args) == 1
                assert call_args[0].id == 1001
                assert call_args[0].name_en == "Anvil Rock"

    @pytest.mark.asyncio
    async def test_sync_worlds_to_db_handles_errors(
            self,
            worlds_service
    ):
        """Test: _sync_worlds_to_db handles errors without propagating exception"""
        # Arrange
        worlds_data = [
            WorldDTO(
                id=1001,
                name_en="Test",
                name_es="Prueba",
                name_de="Test",
                name_fr="Test"
            )
        ]

        with patch('app.services.worlds_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB error")

            # Act (should not raise exception)
            await worlds_service._sync_worlds_to_db(worlds_data)

            # Assert - function should handle error without propagating it
            assert True  # If we reach here, exception was not propagated
