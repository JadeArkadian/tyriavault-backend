from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.database.models import GameAccounts, Worlds
from app.gw2.responses import GW2ApiAccount
from app.services.account_service import AccountService
from app.services.dtos.account_dto import AccountDTO


@pytest.fixture
def mock_account_repository():
    """Mock repository for account"""
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
def sample_api_account_response():
    """Sample account response from GW2 API"""
    return GW2ApiAccount(
        id="12345678-1234-1234-1234-123456789abc",
        name="TestAccount.1234",
        age=300000000,  # Age in seconds
        world=2001,
        guilds=["guild-uuid-1", "guild-uuid-2"],
        guild_leader=["guild-uuid-1"],
        created=datetime(2015, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
        access=["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"],
        commander=True,
        fractal_level=75,
        daily_ap=5000,
        monthly_ap=500,
        wvw_rank=1250
    )


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
def sample_game_account(sample_account_uuid):
    """Sample game account from database"""
    account = MagicMock(spec=GameAccounts)
    account.uuid = sample_account_uuid
    account.account_name = "TestAccount.1234"
    account.world_id = 2001
    account.creation_date = datetime(2015, 6, 23, 12, 0, 0, tzinfo=timezone.utc)
    account.fractal_level = 75
    account.content_access = ["PlayForFree", "GuildWars2", "HeartOfThorns"]
    account.last_modified = datetime.now(timezone.utc)
    account.last_fetched = datetime.now(timezone.utc)
    return account


class TestAccountService:
    """Test suite for AccountService"""

    @pytest.mark.asyncio
    async def test_get_account_details_success_from_api(
            self,
            account_service,
            mock_gw2_client,
            mock_worlds_repository,
            sample_account_uuid,
            sample_api_account_response,
            sample_world
    ):
        """Test: successfully obtain account from the API"""
        # Arrange
        mock_gw2_client.get_account.return_value = sample_api_account_response
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        with patch.object(account_service, '_sync_account_to_db', new_callable=AsyncMock):
            result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountDTO)
        assert result.uuid == UUID("12345678-1234-1234-1234-123456789abc")
        assert result.account_name == "TestAccount.1234"
        assert result.world_id == 2001
        assert result.fractal_level == 75
        assert result.content_access == ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]

        # Verify world info was embedded
        assert result.world_name_en == "Anvil Rock"
        assert result.world_name_es == "Roca del Yunque"
        assert result.world_name_de == "Ambossfelsen"
        assert result.world_name_fr == "Rocher de l'enclume"

        # Verify that the API was called
        mock_gw2_client.get_account.assert_called_once()
        mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_get_account_details_fallback_to_db(
            self,
            account_service,
            mock_gw2_client,
            mock_account_repository,
            mock_worlds_repository,
            sample_account_uuid,
            sample_game_account,
            sample_world
    ):
        """Test: fallback to the database when the API fails"""
        # Arrange
        mock_gw2_client.get_account.side_effect = Exception("API Error")
        mock_account_repository.get_by_uuid.return_value = sample_game_account
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service.get_account_details(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountDTO)
        assert result.uuid == sample_account_uuid
        assert result.account_name == "TestAccount.1234"
        assert result.world_id == 2001
        assert result.fractal_level == 75

        # Verify world info was embedded
        assert result.world_name_en == "Anvil Rock"

        # Verify that the repository was called
        mock_account_repository.get_by_uuid.assert_called_once_with(sample_account_uuid)
        mock_worlds_repository.get_by_id.assert_called_once_with(2001)

    @pytest.mark.asyncio
    async def test_get_account_from_db_no_account_raises_error(
            self,
            account_service,
            mock_gw2_client,
            mock_account_repository,
            sample_account_uuid
    ):
        """Test: raise error when account not found in DB"""
        # Arrange
        mock_gw2_client.get_account.side_effect = Exception("API Error")
        mock_account_repository.get_by_uuid.return_value = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="No account data available from API or database"):
            await account_service.get_account_details(sample_account_uuid)

    @pytest.mark.asyncio
    async def test_build_dto_without_world(
            self,
            account_service,
            mock_worlds_repository,
            sample_api_account_response
    ):
        """Test: _build_dto handles missing world gracefully"""
        # Arrange
        mock_worlds_repository.get_by_id.return_value = None

        # Act
        result = await account_service._build_dto(sample_api_account_response)

        # Assert
        assert isinstance(result, AccountDTO)
        assert result.uuid == UUID("12345678-1234-1234-1234-123456789abc")
        assert result.world_id == 2001
        # World names should be None
        assert result.world_name_en is None
        assert result.world_name_es is None
        assert result.world_name_de is None
        assert result.world_name_fr is None

    @pytest.mark.asyncio
    async def test_sync_account_to_db_success(
            self,
            account_service,
            sample_api_account_response
    ):
        """Test: successfully sync account to database"""
        # Arrange
        mock_session = AsyncMock()
        mock_repo = AsyncMock()

        with patch('app.services.account_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.account_service.AccountRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Act
                await account_service._sync_account_to_db(sample_api_account_response)

                # Assert
                assert mock_repo.upsert.call_count == 1
                call_args = mock_repo.upsert.call_args[0][0]
                # Verify ORM object
                assert call_args.uuid == UUID("12345678-1234-1234-1234-123456789abc")
                assert call_args.account_name == "TestAccount.1234"
                assert call_args.world_id == 2001
                assert call_args.fractal_level == 75

    @pytest.mark.asyncio
    async def test_sync_account_to_db_handles_errors(
            self,
            account_service,
            sample_api_account_response
    ):
        """Test: _sync_account_to_db handles errors gracefully"""
        # Arrange
        with patch('app.services.account_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB error")

            # Act (should not raise exception)
            await account_service._sync_account_to_db(sample_api_account_response)

            # Assert - function should handle error without propagating it
            assert True  # If we reach here, exception was not propagated

    @pytest.mark.asyncio
    async def test_get_account_from_db_converts_orm_to_dto(
            self,
            account_service,
            mock_account_repository,
            mock_worlds_repository,
            sample_account_uuid,
            sample_game_account,
            sample_world
    ):
        """Test: _get_account_from_db correctly converts ORM to DTO"""
        # Arrange
        mock_account_repository.get_by_uuid.return_value = sample_game_account
        mock_worlds_repository.get_by_id.return_value = sample_world

        # Act
        result = await account_service._get_account_from_db(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountDTO)
        assert hasattr(result, 'uuid')
        assert hasattr(result, 'account_name')
        assert hasattr(result, 'world_id')
        assert hasattr(result, 'fractal_level')
        assert hasattr(result, 'content_access')
        assert hasattr(result, 'world_name_en')

    @pytest.mark.asyncio
    async def test_get_account_from_db_without_world(
            self,
            account_service,
            mock_account_repository,
            mock_worlds_repository,
            sample_account_uuid,
            sample_game_account
    ):
        """Test: handle account without world_id"""
        # Arrange
        sample_game_account.world_id = None
        mock_account_repository.get_by_uuid.return_value = sample_game_account

        # Act
        result = await account_service._get_account_from_db(sample_account_uuid)

        # Assert
        assert isinstance(result, AccountDTO)
        assert result.world_id is None
        assert result.world_name_en is None
        # worlds repository should not be called
        mock_worlds_repository.get_by_id.assert_not_called()
