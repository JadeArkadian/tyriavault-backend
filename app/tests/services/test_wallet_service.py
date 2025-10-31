from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.api.v1.responses.wallet_response import WalletItemResponse
from app.database.models import Currencies, Wallet
from app.gw2.responses.gw2api_wallet import GW2ApiWalletEntry
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
        assert isinstance(result[0], WalletItemResponse)

        # Check first currency (Coin)
        assert result[0].currency_id == 1
        assert result[0].amount == 1234567
        assert result[0].currency_name["en"] == "Coin"
        assert result[0].currency_name["es"] == "Moneda"
        assert result[0].currency_icon == "https://example.com/coin.png"

        # Check second currency (Karma)
        assert result[1].currency_id == 2
        assert result[1].amount == 500000
        assert result[1].currency_name["en"] == "Karma"

        # Check third currency (Gems)
        assert result[2].currency_id == 4
        assert result[2].amount == 125
        assert result[2].currency_name["en"] == "Gems"

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
        assert isinstance(result[0], WalletItemResponse)

        # Check first currency
        assert result[0].currency_id == 1
        assert result[0].amount == 1234567
        assert result[0].currency_name["en"] == "Coin"

        # Check second currency
        assert result[1].currency_id == 2
        assert result[1].amount == 500000

        # Verify that the repository was called
        mock_wallet_repository.get_wallet_by_account_uuid.assert_called_once_with(sample_account_uuid)

        # Verify that the API was tried first
        mock_gw2_client.get_wallet.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_wallet_empty_from_db(
            self,
            wallet_service,
            mock_gw2_client,
            mock_wallet_repository,
            sample_account_uuid
    ):
        """Test: return empty list when database has no wallet data"""
        # Arrange
        mock_gw2_client.get_wallet.side_effect = Exception("API Error")
        mock_wallet_repository.get_wallet_by_account_uuid.return_value = []

        # Act
        result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert result == []
        mock_wallet_repository.get_wallet_by_account_uuid.assert_called_once_with(sample_account_uuid)

    @pytest.mark.asyncio
    async def test_get_wallet_with_missing_currency(
            self,
            wallet_service,
            mock_gw2_client,
            mock_currencies_repository,
            sample_account_uuid
    ):
        """Test: skip wallet entries when currency is not found in database"""
        # Arrange
        wallet_response = [
            GW2ApiWalletEntry(id=1, value=1000),
            GW2ApiWalletEntry(id=999, value=500),  # Currency not in database
        ]

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

        mock_gw2_client.get_wallet.return_value = wallet_response
        mock_currencies_repository.get_all.return_value = [currency1]

        # Act
        with patch.object(wallet_service, '_sync_wallet_to_db', new_callable=AsyncMock):
            result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        # Only one currency should be returned (currency 999 is skipped)
        assert len(result) == 1
        assert result[0].currency_id == 1
        assert result[0].amount == 1000

    @pytest.mark.asyncio
    async def test_get_wallet_empty_response_from_api(
            self,
            wallet_service,
            mock_gw2_client,
            mock_currencies_repository,
            sample_account_uuid
    ):
        """Test: return empty list when API returns empty wallet"""
        # Arrange
        mock_gw2_client.get_wallet.return_value = []
        mock_currencies_repository.get_all.return_value = []

        # Act
        with patch.object(wallet_service, '_sync_wallet_to_db', new_callable=AsyncMock):
            result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert result == []
        mock_gw2_client.get_wallet.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_response_with_complete_data(
            self,
            wallet_service,
            mock_currencies_repository,
            sample_api_wallet_response,
            sample_currencies_from_db
    ):
        """Test: _build_response creates proper response with complete data"""
        # Arrange
        mock_currencies_repository.get_all.return_value = sample_currencies_from_db

        # Act
        result = await wallet_service._build_response(sample_api_wallet_response)

        # Assert
        assert len(result) == 3

        # Verify first item structure
        assert isinstance(result[0], WalletItemResponse)
        assert result[0].currency_id == 1
        assert result[0].amount == 1234567
        assert result[0].currency_name == {
            "es": "Moneda",
            "en": "Coin",
            "fr": "Pièce",
            "de": "Münze"
        }
        assert result[0].currency_description == {
            "es": "La moneda principal",
            "en": "The primary currency",
            "fr": "La monnaie principale",
            "de": "Die Hauptwährung"
        }
        assert result[0].currency_icon == "https://example.com/coin.png"

    @pytest.mark.asyncio
    async def test_sync_wallet_to_db(
            self,
            wallet_service,
            sample_account_uuid,
            sample_api_wallet_response
    ):
        """Test: _sync_wallet_to_db prepares correct data for upsert"""
        # Arrange
        mock_session = AsyncMock()
        mock_wallet_repo = AsyncMock()

        # Act
        with patch('app.services.wallet_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.wallet_service.WalletRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_wallet_repo

                await wallet_service._sync_wallet_to_db(sample_api_wallet_response, sample_account_uuid)

        # Assert
        mock_wallet_repo.upsert_batch.assert_awaited_once()

        # Verify the data structure passed to upsert_batch
        call_args = mock_wallet_repo.upsert_batch.call_args[0][0]
        assert len(call_args) == 3
        assert call_args[0] == {
            'currency_id': 1,
            'game_account_uuid': sample_account_uuid,
            'amount': 1234567
        }
        assert call_args[1] == {
            'currency_id': 2,
            'game_account_uuid': sample_account_uuid,
            'amount': 500000
        }
        assert call_args[2] == {
            'currency_id': 4,
            'game_account_uuid': sample_account_uuid,
            'amount': 125
        }

        # Verify commit was called
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_wallet_from_db_with_null_amount(
            self,
            wallet_service,
            mock_gw2_client,
            mock_wallet_repository,
            sample_account_uuid,
            sample_currencies_from_db
    ):
        """Test: handle null amounts in database wallet entries"""
        # Arrange
        wallet_entry = MagicMock(spec=Wallet)
        wallet_entry.currency_id = 1
        wallet_entry.game_account_uuid = sample_account_uuid
        wallet_entry.amount = None  # Null amount
        wallet_entry.currency = sample_currencies_from_db[0]

        mock_gw2_client.get_wallet.side_effect = Exception("API Error")
        mock_wallet_repository.get_wallet_by_account_uuid.return_value = [wallet_entry]

        # Act
        result = await wallet_service.get_wallet(sample_account_uuid)

        # Assert
        assert len(result) == 1
        assert result[0].amount == 0  # Should default to 0

    @pytest.mark.asyncio
    async def test_sync_wallet_error_handling(
            self,
            wallet_service,
            sample_account_uuid,
            sample_api_wallet_response
    ):
        """Test: _sync_wallet_to_db handles errors gracefully"""
        # Arrange
        with patch('app.services.wallet_service.async_session_maker') as mock_session_maker:
            mock_session_maker.side_effect = Exception("Database connection error")

            # Act & Assert - should not raise exception
            await wallet_service._sync_wallet_to_db(sample_api_wallet_response, sample_account_uuid)

            # The method should log the error but not raise it
            # (background tasks should not crash the main request)
