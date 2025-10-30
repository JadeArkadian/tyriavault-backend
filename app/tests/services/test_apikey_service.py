from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.database.models import ApiKeys, GameAccounts, Worlds
from app.services.apikey_service import ApiKeyService


@pytest.fixture
def mock_apikeys_repository():
    """Mock repository for API keys"""
    repository = AsyncMock()
    repository.session = AsyncMock()
    repository.session.commit = AsyncMock()
    return repository


@pytest.fixture
def mock_worlds_repository():
    """Mock repository for worlds"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def apikey_service(mock_apikeys_repository, mock_worlds_repository):
    """Fixture for API key service"""
    return ApiKeyService(
        api_keys_repository=mock_apikeys_repository,
        worlds_repository=mock_worlds_repository
    )


@pytest.fixture
def sample_api_key():
    """Sample API key"""
    return "AAAABBBB-1111-2222-3333-444444444444-5555-6666-7777-888888888888"


@pytest.fixture
def sample_account_uuid():
    """Sample account UUID"""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def sample_token_info():
    """Sample token info from GW2 API"""
    return {
        "id": "test-token-id",
        "name": "My API Key",
        "permissions": ["account", "inventories", "characters", "wallet"]
    }


@pytest.fixture
def sample_account_data():
    """Sample account data from GW2 API"""
    return {
        "id": "12345678-1234-1234-1234-123456789abc",
        "name": "TestAccount.1234",
        "world": 2001,
        "created": "2015-06-16T04:31:00Z",
        "fractal_level": 75,
        "access": ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"],
        "last_modified": "2023-12-01T10:00:00Z"
    }


@pytest.fixture
def sample_world():
    """Sample world from database"""
    world = MagicMock(spec=Worlds)
    world.id = 2001
    world.name_en = "Anvil Rock"
    world.name_es = "Roca del Yunque"
    world.name_de = "Ambossfelsen"
    world.name_fr = "Rocher de l'enclume"
    return world


@pytest.fixture
def sample_apikey_record(sample_api_key, sample_account_uuid):
    """Sample API key record from database"""
    record = MagicMock(spec=ApiKeys)
    record.api_key = sample_api_key
    record.permissions = ["account", "inventories", "characters"]
    record.game_account_uuid = sample_account_uuid
    record.last_fetched = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return record


class TestApiKeyService:
    """Test suite for ApiKeyService"""

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_success(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key,
            sample_apikey_record,
            sample_account_uuid
    ):
        """Test: successfully retrieve API key data from database"""
        # Arrange
        mock_apikeys_repository.get_by_apikey.return_value = sample_apikey_record

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert result is not None
        assert result["api_key"] == sample_api_key
        assert result["permissions"] == ["account", "inventories", "characters"]
        assert result["game_account_uuid"] == sample_account_uuid

        # Verify repository was called
        mock_apikeys_repository.get_by_apikey.assert_called_once_with(sample_api_key)

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_not_found(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key
    ):
        """Test: return None when API key is not found in database"""
        # Arrange
        mock_apikeys_repository.get_by_apikey.return_value = None

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert result is None
        mock_apikeys_repository.get_by_apikey.assert_called_once_with(sample_api_key)

    @pytest.mark.asyncio
    async def test_get_apikey_data_from_db_with_null_permissions(
            self,
            apikey_service,
            mock_apikeys_repository,
            sample_api_key
    ):
        """Test: handle API key with null permissions"""
        # Arrange
        record = MagicMock(spec=ApiKeys)
        record.api_key = sample_api_key
        record.permissions = None  # Null permissions
        record.game_account_uuid = UUID("00000000-0000-0000-0000-000000000000")
        mock_apikeys_repository.get_by_apikey.return_value = record

        # Act
        result = await apikey_service.get_apikey_data_from_db(sample_api_key)

        # Assert
        assert result is not None
        assert result["permissions"] == []  # Should default to empty list

    @pytest.mark.asyncio
    async def test_validate_and_register_success(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_account_data,
            sample_world
    ):
        """Test: successfully validate and register a new API key"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Mock GW2Client
        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert result["api_key"] == sample_api_key
            assert result["permissions"] == ["account", "inventories", "characters", "wallet"]
            assert result["game_account_uuid"] == UUID("12345678-1234-1234-1234-123456789abc")
            assert result["account_name"] == "TestAccount.1234"

            # Verify GW2 client was called
            mock_client.token_info.assert_called_once()
            mock_client.get_account.assert_called_once()

            # Verify world exists check
            mock_worlds_repository.get_by_id.assert_called_once_with(2001)

            # Verify upsert operations
            mock_apikeys_repository.upsert_game_account.assert_called_once()
            mock_apikeys_repository.upsert.assert_called_once()
            mock_apikeys_repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_register_world_not_found(
            self,
            apikey_service,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_account_data
    ):
        """Test: raise error when world doesn't exist in database"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = None

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(RuntimeError, match="World ID 2001 doesn't exist in database"):
                await apikey_service.validate_and_register(sample_api_key)

            # Verify world check was performed
            mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_validate_and_register_without_world(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info
    ):
        """Test: successfully register API key when account has no world"""
        # Arrange
        account_data_no_world = {
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "NoWorldAccount.5678",
            "world": None,  # No world
            "created": "2020-01-01T00:00:00Z",
            "fractal_level": 1,
            "access": ["PlayForFree"],
            "last_modified": "2023-01-01T00:00:00Z"
        }

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = account_data_no_world
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert result["api_key"] == sample_api_key
            assert result["account_name"] == "NoWorldAccount.5678"

            # Verify world check was not performed
            mock_worlds_repository.get_by_id.assert_not_called()

            # Verify upsert operations
            mock_apikeys_repository.upsert_game_account.assert_called_once()
            mock_apikeys_repository.upsert.assert_called_once()
            mock_apikeys_repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_register_invalid_api_key(
            self,
            apikey_service,
            sample_api_key
    ):
        """Test: raise error when API key is invalid"""
        # Arrange
        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.side_effect = Exception("Invalid API key")
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(Exception, match="Invalid API key"):
                await apikey_service.validate_and_register(sample_api_key)

    @pytest.mark.asyncio
    async def test_validate_and_register_api_error_during_account_fetch(
            self,
            apikey_service,
            sample_api_key,
            sample_token_info
    ):
        """Test: raise error when fetching account data fails"""
        # Arrange
        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.side_effect = Exception("Account fetch failed")
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(Exception, match="Account fetch failed"):
                await apikey_service.validate_and_register(sample_api_key)

    @pytest.mark.asyncio
    async def test_validate_and_register_with_minimal_permissions(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_account_data,
            sample_world
    ):
        """Test: register API key with minimal permissions"""
        # Arrange
        minimal_token_info = {
            "id": "test-token-id",
            "name": "Minimal Key",
            "permissions": ["account"]  # Only account permission
        }

        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = minimal_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert result["permissions"] == ["account"]
            mock_apikeys_repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_register_with_empty_permissions(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_account_data,
            sample_world
    ):
        """Test: register API key with no permissions"""
        # Arrange
        no_permissions_token = {
            "id": "test-token-id",
            "name": "No Permissions Key",
            "permissions": []  # No permissions
        }

        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = no_permissions_token
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert result["permissions"] == []
            mock_apikeys_repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_register_upsert_game_account_called_with_correct_data(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_account_data,
            sample_world
    ):
        """Test: verify game account upsert is called with correct data"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act
            await apikey_service.validate_and_register(sample_api_key)

            # Assert - Verify upsert_game_account was called
            mock_apikeys_repository.upsert_game_account.assert_called_once()

            # Get the GameAccounts object that was passed
            call_args = mock_apikeys_repository.upsert_game_account.call_args[0][0]
            assert isinstance(call_args, GameAccounts)
            assert call_args.uuid == UUID("12345678-1234-1234-1234-123456789abc")
            assert call_args.account_name == "TestAccount.1234"
            assert call_args.world_id == 2001
            assert call_args.fractal_level == 75
            assert call_args.content_access == ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]

    @pytest.mark.asyncio
    async def test_validate_and_register_upsert_apikey_called_with_correct_data(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_account_data,
            sample_world
    ):
        """Test: verify API key upsert is called with correct data"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act
            await apikey_service.validate_and_register(sample_api_key)

            # Assert - Verify upsert was called
            mock_apikeys_repository.upsert.assert_called_once()

            # Get the ApiKeys object that was passed
            call_args = mock_apikeys_repository.upsert.call_args[0][0]
            assert isinstance(call_args, ApiKeys)
            assert call_args.api_key == sample_api_key
            assert call_args.permissions == ["account", "inventories", "characters", "wallet"]
            assert call_args.game_account_uuid == UUID("12345678-1234-1234-1234-123456789abc")

    @pytest.mark.asyncio
    async def test_validate_and_register_without_last_modified(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_world
    ):
        """Test: handle account data without last_modified field"""
        # Arrange
        account_data_no_last_modified = {
            "id": "12345678-1234-1234-1234-123456789abc",
            "name": "TestAccount.1234",
            "world": 2001,
            "created": "2015-06-16T04:31:00Z",
            "fractal_level": 75,
            "access": ["PlayForFree", "GuildWars2"]
            # No last_modified field
        }

        mock_worlds_repository.get_by_id.return_value = sample_world

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = account_data_no_last_modified
            mock_gw2_client_class.return_value = mock_client

            # Act
            result = await apikey_service.validate_and_register(sample_api_key)

            # Assert
            assert result["api_key"] == sample_api_key
            assert result["account_name"] == "TestAccount.1234"

            # Verify upsert operations completed
            mock_apikeys_repository.upsert_game_account.assert_called_once()
            mock_apikeys_repository.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_and_register_database_commit_error(
            self,
            apikey_service,
            mock_apikeys_repository,
            mock_worlds_repository,
            sample_api_key,
            sample_token_info,
            sample_account_data,
            sample_world
    ):
        """Test: handle database commit errors"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = sample_world
        mock_apikeys_repository.session.commit.side_effect = Exception("Database commit failed")

        with patch('app.services.apikey_service.GW2Client') as mock_gw2_client_class:
            mock_client = AsyncMock()
            mock_client.token_info.return_value = sample_token_info
            mock_client.get_account.return_value = sample_account_data
            mock_gw2_client_class.return_value = mock_client

            # Act & Assert
            with pytest.raises(Exception, match="Database commit failed"):
                await apikey_service.validate_and_register(sample_api_key)
