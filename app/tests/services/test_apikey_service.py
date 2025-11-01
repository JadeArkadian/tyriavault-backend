from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.database.models import ApiKeys, Worlds
from app.gw2.responses import GW2ApiAccount, GW2ApiTokenInfo
from app.services.apikey_service import ApiKeyService
from app.services.dtos.apikey_dto import ApiKeyDTO


@pytest.fixture
def mock_apikeys_repository():
    """Mock repository for api keys"""
    repository = AsyncMock()
    repository.session = AsyncMock()
    return repository


@pytest.fixture
def mock_worlds_repository():
    """Mock repository for worlds"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def apikey_service(mock_apikeys_repository, mock_worlds_repository):
    """Fixture for apikey service"""
    return ApiKeyService(
        api_keys_repository=mock_apikeys_repository,
        worlds_repository=mock_worlds_repository
    )


@pytest.fixture
def sample_api_key():
    """Sample API key"""
    return "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXXXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"


@pytest.fixture
def sample_account_uuid():
    """Sample account UUID"""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def sample_apikey_record(sample_api_key, sample_account_uuid):
    """Sample API key record from database"""
    apikey = MagicMock(spec=ApiKeys)
    apikey.api_key = sample_api_key
    apikey.permissions = ["account", "characters", "inventories", "wallet"]
    apikey.game_account_uuid = sample_account_uuid
    return apikey


@pytest.fixture
def sample_token_info():
    """Sample token info from GW2 API"""
    return GW2ApiTokenInfo(
        id="test-token-id",
        name="Test Token",
        permissions=["account", "characters", "inventories", "wallet"]
    )


@pytest.fixture
def sample_gw2_account():
    """Sample account from GW2 API"""
    return GW2ApiAccount(
        id="12345678-1234-1234-1234-123456789abc",
        name="TestAccount.1234",
        age=300000000,
        world=2001,
        guilds=[],
        guild_leader=[],
        created=datetime(2015, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        access=["PlayForFree", "GuildWars2"],
        commander=False,
        fractal_level=50,
        daily_ap=1000,
        monthly_ap=100,
        wvw_rank=500
    )


@pytest.fixture
def sample_world():
    """Sample world from database"""
    world = MagicMock(spec=Worlds)
    world.id = 2001
    world.name_en = "Anvil Rock"
    return world


class TestApiKeyService:
    """Test suite for ApiKeyService"""

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_success(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key,
            sample_apikey_record
    ):
        """Test: successfully get API key from database"""
        # Arrange
        mock_apikeys_repository.get_by_apikey.return_value = sample_apikey_record

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert isinstance(result, ApiKeyDTO)
        assert result.api_key == sample_api_key
        assert result.permissions == ["account", "characters", "inventories", "wallet"]
        assert result.game_account_uuid == UUID("12345678-1234-1234-1234-123456789abc")
        mock_apikeys_repository.get_by_apikey.assert_called_once_with(sample_api_key)

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_not_found(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key
    ):
        """Test: return None when API key not found in database"""
        # Arrange
        mock_apikeys_repository.get_by_apikey.return_value = None

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert result is None
        mock_apikeys_repository.get_by_apikey.assert_called_once_with(sample_api_key)

    @pytest.mark.asyncio
    async def test_validate_and_register_success(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_gw2_account,
            sample_world
    ):
        """Test: successfully validate and register new API key"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_gw2_account
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert isinstance(result, ApiKeyDTO)
            assert result.api_key == sample_api_key
            assert result.permissions == ["account", "characters", "inventories", "wallet"]
            assert result.game_account_uuid == UUID("12345678-1234-1234-1234-123456789abc")
            assert result.account_name == "TestAccount.1234"

            # Verify repositories were called
            mock_apikeys_repository.upsert_game_account.assert_called_once()
            mock_apikeys_repository.upsert.assert_called_once()
            mock_apikeys_repository.session.commit.assert_called_once()
            mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_validate_and_register_world_not_found(
            self,
            apikey_service,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_gw2_account
    ):
        """Test: raise error when world not found in database"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = None

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_gw2_account
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(RuntimeError, match="World ID 2001 doesn't exist in database"):
                await apikey_service.validate_and_register(sample_api_key)

    @pytest.mark.asyncio
    async def test_validate_and_register_account_without_world(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_gw2_account
    ):
        """Test: successfully register API key when account has no world"""
        # Arrange
        sample_gw2_account.world = None

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_gw2_account
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert isinstance(result, ApiKeyDTO)
            assert result.api_key == sample_api_key
            # worlds_repository should not be called
            mock_worlds_repository.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_and_register_gw2_api_error(
            self,
            apikey_service,
            sample_api_key
    ):
        """Test: propagate GW2 API errors"""
        # Arrange
        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.side_effect = Exception("Invalid API key")
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(Exception, match="Invalid API key"):
                await apikey_service.validate_and_register(sample_api_key)

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_with_empty_permissions(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key,
            sample_apikey_record
    ):
        """Test: handle API key with None permissions"""
        # Arrange
        sample_apikey_record.permissions = None
        mock_apikeys_repository.get_by_apikey.return_value = sample_apikey_record

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert isinstance(result, ApiKeyDTO)
        assert result.permissions == []  # Should default to empty list
