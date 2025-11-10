from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.database.models import Currencies, Wallet
from app.gw2.responses.gw2api_wallet import GW2ApiWalletEntry
from app.services.dtos.wallet_dto import WalletItemDTO
from app.services.wallet_service import WalletService


@pytest.fixture
def mock_wallet_repository():
    """Mock repository for wallet"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_currencies_repository():
    """Mock repository for currencies"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock GW2 client"""
    client = AsyncMock()
    return client


@pytest.fixture
def wallet_service(mock_wallet_repository, mock_currencies_repository, mock_gw2_client):
    """Fixture for wallet service"""
    return WalletService(
        wallet_repository=mock_wallet_repository,
        currencies_repository=mock_currencies_repository,
        gw2_client=mock_gw2_client
    )


@pytest.fixture
def sample_account_uuid():
    """Sample account UUID"""
    return UUID("12345678-1234-1234-1234-123456789abc")


@pytest.fixture
def sample_api_wallet_response():
    """Sample wallet response from GW2 API"""
    return [
        GW2ApiWalletEntry(id=1, value=1234567),
        GW2ApiWalletEntry(id=2, value=500000),
        GW2ApiWalletEntry(id=4, value=125)
    ]


@pytest.fixture
def sample_currencies_from_db():
    """Sample currencies from the database"""
    currency1 = MagicMock(spec=Currencies)
    currency1.id = 1
    currency1.name_en = "Coin"
    currency1.name_es = "Moneda"
    currency1.name_de = "Münze"
    currency1.name_fr = "Pièce"
    currency1.description_en = "The primary currency"
    currency1.description_es = "La moneda principal"
    currency1.description_de = "Die Hauptwährung"
    currency1.description_fr = "La monnaie principale"
    currency1.icon_url = "https://example.com/coin.png"

    currency2 = MagicMock(spec=Currencies)
    currency2.id = 2
    currency2.name_en = "Karma"
    currency2.name_es = "Karma"
    currency2.name_de = "Karma"
    currency2.name_fr = "Karma"
    currency2.description_en = "Earned by helping others"
    currency2.description_es = "Ganado ayudando a otros"
    currency2.description_de = "Verdient durch Hilfe für andere"
    currency2.description_fr = "Gagné en aidant les autres"
    currency2.icon_url = "https://example.com/karma.png"

    currency3 = MagicMock(spec=Currencies)
    currency3.id = 4
    currency3.name_en = "Gems"
    currency3.name_es = "Gemas"
    currency3.name_de = "Edelsteine"
    currency3.name_fr = "Gemmes"
    currency3.description_en = "Premium currency"
    currency3.description_es = "Moneda premium"
    currency3.description_de = "Premium-Währung"
    currency3.description_fr = "Monnaie premium"
    currency3.icon_url = "https://example.com/gems.png"

    return [currency1, currency2, currency3]


@pytest.fixture
def sample_wallet_from_db(sample_account_uuid, sample_currencies_from_db):
    """Sample wallet entries from the database"""
    wallet1 = MagicMock(spec=Wallet)
    wallet1.currency_id = 1
    wallet1.game_account_uuid = sample_account_uuid
    wallet1.amount = 1234567
    wallet1.currency = sample_currencies_from_db[0]

    wallet2 = MagicMock(spec=Wallet)
    wallet2.currency_id = 2
    wallet2.game_account_uuid = sample_account_uuid
    wallet2.amount = 500000
    wallet2.currency = sample_currencies_from_db[1]

    wallet3 = MagicMock(spec=Wallet)
    wallet3.currency_id = 4
    wallet3.game_account_uuid = sample_account_uuid
    wallet3.amount = 125
    wallet3.currency = sample_currencies_from_db[2]

    return [wallet1, wallet2, wallet3]


class TestWalletService:
    """Test suite for WalletService"""

    @pytest.mark.asyncio
    async def test_get_wallet_success_from_api(
            self,
            wallet_service,
            mock_gw2_client,
            mock_currencies_repository,
            sample_account_uuid,
            sample_api_wallet_response,
            sample_currencies_from_db
    ):
        """Test: successfully obtain wallet from the API"""
        # Arrange
        mock_gw2_client.get_wallet.return_value = sample_api_wallet_response
        mock_currencies_repository.get_all.return_value = sample_currencies_from_db

        # Act
        with patch.object(wallet_service, '_sync_wallet_to_db', new_callable=AsyncMock):
            result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert len(result) == 3
        assert isinstance(result[0], WalletItemDTO)

        # Check first currency (Coin)
        assert result[0].currency_id == 1
        assert result[0].amount == 1234567
        assert result[0].currency_name_en == "Coin"
        assert result[0].currency_name_es == "Moneda"
        assert result[0].currency_icon_url == "https://example.com/coin.png"

        # Check second currency (Karma)
        assert result[1].currency_id == 2
        assert result[1].amount == 500000
        assert result[1].currency_name_en == "Karma"

        # Check third currency (Gems)
        assert result[2].currency_id == 4
        assert result[2].amount == 125
        assert result[2].currency_name_en == "Gems"

        # Verify that the API was called
        mock_gw2_client.get_wallet.assert_called_once()

        # Verify that currencies were fetched from repository
        mock_currencies_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_wallet_fallback_to_db(
            self,
            wallet_service,
            mock_gw2_client,
            mock_wallet_repository,
            sample_account_uuid,
            sample_wallet_from_db
    ):
        """Test: fallback to the database when the API fails"""
        # Arrange
        mock_gw2_client.get_wallet.side_effect = Exception("API Error")
        mock_wallet_repository.get_wallet_by_account_uuid.return_value = sample_wallet_from_db

        # Act
        result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert len(result) == 3
        assert isinstance(result[0], WalletItemDTO)

        # Check first currency
        assert result[0].currency_id == 1
        assert result[0].amount == 1234567
        assert result[0].currency_name_en == "Coin"

        # Check second currency
        assert result[1].currency_id == 2
        assert result[1].amount == 500000

        # Verify that the repository was called
        mock_wallet_repository.get_wallet_by_account_uuid.assert_called_once_with(sample_account_uuid)

    @pytest.mark.asyncio
    async def test_get_wallet_from_db_empty(
            self,
            wallet_service,
            mock_gw2_client,
            mock_wallet_repository,
            sample_account_uuid
    ):
        """Test: return empty list when wallet is empty in DB"""
        # Arrange
        mock_gw2_client.get_wallet.side_effect = Exception("API Error")
        mock_wallet_repository.get_wallet_by_account_uuid.return_value = []

        # Act
        result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_build_response_skips_unknown_currencies(
            self,
            wallet_service,
            mock_currencies_repository,
            sample_api_wallet_response,
            sample_currencies_from_db
    ):
        """Test: _build_response skips currencies not found in DB"""
        # Arrange
        # Add a wallet entry with currency ID that doesn't exist in currencies
        wallet_with_unknown = sample_api_wallet_response + [
            GW2ApiWalletEntry(id=999, value=100)  # Unknown currency
        ]
        mock_currencies_repository.get_all.return_value = sample_currencies_from_db

        # Act
        result = await wallet_service._build_response(wallet_with_unknown)

        # Assert
        # Should only return the 3 known currencies, skipping ID 999
        assert len(result) == 3
        currency_ids = [item.currency_id for item in result]
        assert 999 not in currency_ids
        assert 1 in currency_ids
        assert 2 in currency_ids
        assert 4 in currency_ids

    @pytest.mark.asyncio
    async def test_build_response_empty_wallet(self, wallet_service):
        """Test: _build_response returns empty list for empty wallet"""
        # Arrange
        empty_wallet = []

        # Act
        result = await wallet_service._build_response(empty_wallet)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_sync_wallet_to_db_success(
            self,
            wallet_service,
            sample_account_uuid,
            sample_api_wallet_response,
            sample_currencies_from_db
    ):
        """Test: successfully sync wallet to database"""
        # Arrange
        mock_session = AsyncMock()
        mock_wallet_repo = AsyncMock()
        mock_currencies_repo = AsyncMock()
        mock_currencies_repo.get_all.return_value = sample_currencies_from_db

        with patch('app.services.wallet_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.wallet_service.WalletRepository') as mock_wallet_repo_class:
                mock_wallet_repo_class.return_value = mock_wallet_repo
                with patch('app.services.wallet_service.CurrenciesRepository') as mock_currencies_repo_class:
                    mock_currencies_repo_class.return_value = mock_currencies_repo

                    # Act
                    await wallet_service._sync_wallet_to_db(sample_api_wallet_response, sample_account_uuid)

                    # Assert
                    assert mock_wallet_repo.upsert_batch.call_count == 1
                    call_args = mock_wallet_repo.upsert_batch.call_args[0][0]
                    assert len(call_args) == 3
                    # Verify ORM objects
                    assert call_args[0].currency_id == 1
                    assert call_args[0].amount == 1234567
                    assert call_args[0].game_account_uuid == sample_account_uuid

    @pytest.mark.asyncio
    async def test_sync_wallet_to_db_handles_errors(
            self,
            wallet_service,
            sample_account_uuid,
            sample_api_wallet_response
    ):
        """Test: _sync_wallet_to_db handles errors gracefully"""
        # Arrange
        with patch('app.services.wallet_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB error")

            # Act (should not raise exception)
            await wallet_service._sync_wallet_to_db(sample_api_wallet_response, sample_account_uuid)

            # Assert - function should handle error without propagating it
            assert True  # If we reach here, exception was not propagated

    @pytest.mark.asyncio
    async def test_get_wallet_from_db_converts_orm_to_dto(
            self,
            wallet_service,
            mock_wallet_repository,
            sample_account_uuid,
            sample_wallet_from_db
    ):
        """Test: _get_wallet_from_db correctly converts ORM to DTOs"""
        # Arrange
        mock_wallet_repository.get_wallet_by_account_uuid.return_value = sample_wallet_from_db

        # Act
        result = await wallet_service._get_wallet_from_db(sample_account_uuid)

        # Assert
        assert len(result) == 3
        for item in result:
            assert isinstance(item, WalletItemDTO)
            assert hasattr(item, 'currency_id')
            assert hasattr(item, 'amount')
            assert hasattr(item, 'currency_name_en')
            assert hasattr(item, 'currency_icon_url')
