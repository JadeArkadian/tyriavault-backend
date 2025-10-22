from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.api.v1.responses.account_response import AccountInfoResponse
from app.database.models import GameAccounts, Worlds
from app.services.account_service import AccountService


@pytest.fixture
def mock_account_repository():
    """Mock repository for accounts"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_worlds_repository():
    """Mock repository for worlds"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock GW2 client"""
    client = AsyncMock()
    return client


@pytest.fixture
def account_service(mock_account_repository, mock_worlds_repository, mock_gw2_client):
    """Fixture for account service"""
    return AccountService(
        account_repository=mock_account_repository,
        worlds_repository=mock_worlds_repository,
        gw2_client=mock_gw2_client
    )


@pytest.fixture
def sample_account_uuid():
    """Sample account UUID"""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def sample_api_response():
    """Sample response from GW2 API"""
    return {
        "id": "12345678-1234-1234-1234-123456789abc",
        "name": "TestAccount.1234",
        "created": "2015-06-16T04:31:00Z",
        "world": 2001,
        "fractal_level": 75,
        "access": ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"],
        "last_modified": "2023-12-01T10:00:00Z"
    }


@pytest.fixture
def sample_db_account(sample_account_uuid):
    """Sample account from the database"""
    account = MagicMock(spec=GameAccounts)
    account.uuid = sample_account_uuid
    account.account_name = "TestAccount.1234"
    account.world_id = 2001
    account.creation_date = datetime(2015, 6, 16, 4, 31, 0, tzinfo=timezone.utc)
    account.fractal_level = 75
    account.last_modified = datetime(2023, 12, 1, 10, 0, 0, tzinfo=timezone.utc)
    account.content_access = ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]
    account.last_fetched = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return account


@pytest.fixture
def sample_world():
    """Sample world from the database"""
    world = MagicMock(spec=Worlds)
    world.id = 2001
    world.name_en = "Anvil Rock"
    world.name_es = "Roca del Yunque"
    world.name_de = "Ambossfelsen"
    world.name_fr = "Rocher de l'enclume"
    return world


class TestAccountService:
    """Test suite for AccountService"""

    @pytest.mark.asyncio
    async def test_get_account_details_success_from_api(
            self,
            account_service,
            mock_gw2_client,
            mock_worlds_repository,
            sample_account_uuid,
            sample_api_response,
            sample_world
    ):
        """Test: successfully obtain account details from the API"""
        # Arrange
        mock_gw2_client.get_account.return_value = sample_api_response
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == UUID(sample_api_response["id"])
        assert result.account_name == sample_api_response["name"]
        assert result.fractal_level == sample_api_response["fractal_level"]
        assert result.content_access == sample_api_response["access"]
        assert result.world_name["en"] == "Anvil Rock"
        assert result.world_name["es"] == "Roca del Yunque"
        assert result.world_name["de"] == "Ambossfelsen"
        assert result.world_name["fr"] == "Rocher de l'enclume"

        # Verify that the API was called
        mock_gw2_client.get_account.assert_called_once()

        # Verify that the world was fetched
        mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_get_account_details_fallback_to_db(
            self,
            account_service,
            mock_gw2_client,
            mock_account_repository,
            mock_worlds_repository,
            sample_account_uuid,
            sample_db_account,
            sample_world
    ):
        """Test: fallback to the database when the API fails"""
        # Arrange
        mock_gw2_client.get_account.side_effect = Exception("API Error")
        mock_account_repository.get_by_uuid.return_value = sample_db_account
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == sample_account_uuid
        assert result.account_name == "TestAccount.1234"
        assert result.fractal_level == 75
        assert result.content_access == ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]
        assert result.world_name["en"] == "Anvil Rock"

        # Verify that the repository was called
        mock_account_repository.get_by_uuid.assert_called_once_with(sample_account_uuid)

        # Verify that the world was fetched
        mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_get_account_details_without_world(
            self,
            account_service,
            mock_gw2_client,
            mock_worlds_repository,
            sample_account_uuid,
            sample_api_response
    ):
        """Test: account details without world information"""
        # Arrange
        sample_api_response["world"] = None
        mock_gw2_client.get_account.return_value = sample_api_response

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == UUID(sample_api_response["id"])
        assert result.account_name == sample_api_response["name"]
        assert result.world_name["en"] is None
        assert result.world_name["es"] is None
        assert result.world_name["de"] is None
        assert result.world_name["fr"] is None

        # Verify that the world was not fetched
        mock_worlds_repository.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_account_details_world_not_found(
            self,
            account_service,
            mock_gw2_client,
            mock_worlds_repository,
            sample_account_uuid,
            sample_api_response
    ):
        """Test: account details when world is not found in database"""
        # Arrange
        mock_gw2_client.get_account.return_value = sample_api_response
        mock_worlds_repository.get_by_id.return_value = None

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == UUID(sample_api_response["id"])
        assert result.account_name == sample_api_response["name"]
        assert result.world_name["en"] is None
        assert result.world_name["es"] is None
        assert result.world_name["de"] is None
        assert result.world_name["fr"] is None

        # Verify that the world was tried to be fetched
        mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_get_account_details_no_data_available(
            self,
            account_service,
            mock_gw2_client,
            mock_account_repository,
            sample_account_uuid
    ):
        """Test: raise error when no data is available from API or database"""
        # Arrange
        mock_gw2_client.get_account.side_effect = Exception("API Error")
        mock_account_repository.get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="No account data available from API or database"):
            await account_service.get_account_details(sample_account_uuid)

        # Verify that both API and repository were tried
        mock_gw2_client.get_account.assert_called_once()
        mock_account_repository.get_by_uuid.assert_called_once_with(sample_account_uuid)

    @pytest.mark.asyncio
    async def test_sync_account_to_db_creates_background_task(
            self,
            account_service,
            mock_gw2_client,
            mock_worlds_repository,
            sample_account_uuid,
            sample_api_response,
            sample_world
    ):
        """Test: verify that background sync task is created"""
        # Arrange
        mock_gw2_client.get_account.return_value = sample_api_response
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert account_service.task is not None
        assert not account_service.task.done() or account_service.task.done()

        # Wait for background task to complete
        if not account_service.task.done():
            await account_service.task

    @pytest.mark.asyncio
    async def test_build_response_with_complete_world_info(
            self,
            account_service,
            mock_worlds_repository,
            sample_api_response,
            sample_world
    ):
        """Test: _build_response creates proper response with world info"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service._build_response(sample_api_response)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == UUID(sample_api_response["id"])
        assert result.account_name == sample_api_response["name"]
        assert result.world_name["en"] == "Anvil Rock"
        assert result.world_name["es"] == "Roca del Yunque"
        assert result.world_name["de"] == "Ambossfelsen"
        assert result.world_name["fr"] == "Rocher de l'enclume"

    @pytest.mark.asyncio
    async def test_get_account_from_api(
            self,
            account_service,
            mock_gw2_client,
            sample_api_response
    ):
        """Test: _get_account_from_api fetches data from GW2 API"""
        # Arrange
        mock_gw2_client.get_account.return_value = sample_api_response

        # Act
        result = await account_service._get_account_from_api()

        # Assert
        assert result == sample_api_response
        mock_gw2_client.get_account.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_account_from_db(
            self,
            account_service,
            mock_account_repository,
            mock_worlds_repository,
            sample_account_uuid,
            sample_db_account,
            sample_world
    ):
        """Test: _get_account_from_db retrieves account from database"""
        # Arrange
        mock_account_repository.get_by_uuid.return_value = sample_db_account
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service._get_account_from_db(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountInfoResponse)
        assert result.uuid == sample_account_uuid
        assert result.account_name == "TestAccount.1234"
        mock_account_repository.get_by_uuid.assert_called_once_with(sample_account_uuid)
