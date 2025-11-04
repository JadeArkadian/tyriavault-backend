from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.constants import Constants
from app.database.models import Currencies
from app.gw2.responses import GW2ApiCurrency
from app.services.currencies_service import CurrenciesService
from app.services.dtos.currencies_dto import CurrencyDTO


@pytest.fixture
def mock_repository():
    """Mock repository for currencies"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock GW2 client"""
    client = AsyncMock()
    return client


@pytest.fixture
def currencies_service(mock_repository, mock_gw2_client):
    """Fixture for currencies service"""
    return CurrenciesService(repository=mock_repository, gw2_client=mock_gw2_client)


@pytest.fixture
def sample_api_response_en():
    """Sample response from GW2 API in English"""
    return [
        GW2ApiCurrency(
            id=1,
            name="Coin",
            description="The primary currency",
            order=101,
            icon="https://example.com/coin.png"
        ),
        GW2ApiCurrency(
            id=2,
            name="Karma",
            description="Earned by helping others",
            order=102,
            icon="https://example.com/karma.png"
        )
    ]


@pytest.fixture
def sample_api_response_es():
    """Sample response from GW2 API in Spanish"""
    return [
        GW2ApiCurrency(
            id=1,
            name="Moneda",
            description="La moneda principal",
            order=101,
            icon="https://example.com/coin.png"
        ),
        GW2ApiCurrency(
            id=2,
            name="Karma",
            description="Ganado ayudando a otros",
            order=102,
            icon="https://example.com/karma.png"
        )
    ]


@pytest.fixture
def sample_api_response_de():
    """Sample response from GW2 API in German"""
    return [
        GW2ApiCurrency(
            id=1,
            name="Münze",
            description="Die Hauptwährung",
            order=101,
            icon="https://example.com/coin.png"
        ),
        GW2ApiCurrency(
            id=2,
            name="Karma",
            description="Verdient durch Hilfe für andere",
            order=102,
            icon="https://example.com/karma.png"
        )
    ]


@pytest.fixture
def sample_api_response_fr():
    """Sample response from GW2 API in French"""
    return [
        GW2ApiCurrency(
            id=1,
            name="Pièce",
            description="La monnaie principale",
            order=101,
            icon="https://example.com/coin.png"
        ),
        GW2ApiCurrency(
            id=2,
            name="Karma",
            description="Gagné en aidant les autres",
            order=102,
            icon="https://example.com/karma.png"
        )
    ]


@pytest.fixture
def sample_db_currencies():
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

    return [currency1, currency2]


class TestCurrenciesService:
    """Test suite for CurrenciesService"""

    @pytest.mark.asyncio
    async def test_get_all_currencies_success_from_api(
            self,
            currencies_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: successfully obtain currencies from the API"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await currencies_service.get_all_currencies()

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], CurrencyDTO)
        assert result[0].id == 1
        assert result[0].name_en == "Coin"
        assert result[0].name_es == "Moneda"
        assert result[0].name_de == "Münze"
        assert result[0].name_fr == "Pièce"
        assert result[0].icon_url == "https://example.com/coin.png"

        assert isinstance(result[1], CurrencyDTO)
        assert result[1].id == 2
        assert result[1].name_en == "Karma"

        # Verify that the API was called for each language
        assert mock_gw2_client.get_currencies.call_count == 4

    @pytest.mark.asyncio
    async def test_get_all_currencies_fallback_to_db(
            self,
            currencies_service,
            mock_gw2_client,
            mock_repository,
            sample_db_currencies
    ):
        """Test: fallback to the database when the API fails"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = Exception("API Error")
        mock_repository.get_all.return_value = sample_db_currencies

        # Act
        result = await currencies_service.get_all_currencies()

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], CurrencyDTO)
        assert result[0].id == 1
        assert result[0].name_en == "Coin"
        assert result[0].name_es == "Moneda"
        assert isinstance(result[1], CurrencyDTO)
        assert result[1].id == 2

        # Verify that the repository was called
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_currencies_from_api_combines_languages(
            self,
            currencies_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: _get_currencies_from_api correctly combines all languages"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await currencies_service._get_currencies_from_api()

        # Assert
        assert len(result) == 2

        # Verify that the first currency is a DTO with all languages
        currency = result[0]
        assert isinstance(currency, CurrencyDTO)
        assert hasattr(currency, 'name_en')
        assert hasattr(currency, 'name_es')
        assert hasattr(currency, 'name_de')
        assert hasattr(currency, 'name_fr')
        assert hasattr(currency, 'description_en')
        assert hasattr(currency, 'description_es')
        assert hasattr(currency, 'description_de')
        assert hasattr(currency, 'description_fr')
        assert hasattr(currency, 'icon_url')

    @pytest.mark.asyncio
    async def test_get_currencies_from_db_success(
            self,
            currencies_service,
            mock_repository,
            sample_db_currencies
    ):
        """Test: successfully obtain currencies from the database"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_currencies

        # Act
        result = await currencies_service._get_currencies_from_db()

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], CurrencyDTO)
        assert result[0].id == 1
        assert result[0].name_en == "Coin"
        assert result[0].name_es == "Moneda"
        assert result[0].icon_url == "https://example.com/coin.png"

        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_currencies_from_db_empty_raises_error(
            self,
            currencies_service,
            mock_repository
    ):
        """Test: error when the database is empty"""
        # Arrange
        mock_repository.get_all.return_value = []

        # Act & Assert
        with pytest.raises(RuntimeError, match="No currencies available from API or database"):
            await currencies_service._get_currencies_from_db()

    @pytest.mark.asyncio
    async def test_get_currencies_from_db_repository_error(
            self,
            currencies_service,
            mock_repository
    ):
        """Test: error when the repository fails"""
        # Arrange
        mock_repository.get_all.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await currencies_service._get_currencies_from_db()

    @pytest.mark.asyncio
    async def test_sync_currencies_to_db_success(self, currencies_service):
        """Test: successful synchronization of currencies to the database"""
        # Arrange
        currencies_data = [
            CurrencyDTO(
                id=1,
                name_en="Coin",
                name_es="Moneda",
                name_de="Münze",
                name_fr="Pièce",
                description_en="The primary currency",
                description_es="La moneda principal",
                description_de="Die Hauptwährung",
                description_fr="La monnaie principale",
                icon_url="https://example.com/coin.png"
            )
        ]

        mock_session = AsyncMock()
        mock_repo = AsyncMock()

        with patch('app.services.currencies_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch('app.services.currencies_service.CurrenciesRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Act
                await currencies_service._sync_currencies_to_db(currencies_data)

                # Assert - DTOs should be converted to ORM objects before calling upsert_batch
                assert mock_repo.upsert_batch.call_count == 1
                call_args = mock_repo.upsert_batch.call_args[0][0]
                assert len(call_args) == 1
                assert call_args[0].id == 1
                assert call_args[0].name_en == "Coin"

    @pytest.mark.asyncio
    async def test_sync_currencies_to_db_handles_error(self, currencies_service):
        """Test: error handling during synchronization"""
        # Arrange
        currencies_data = [
            CurrencyDTO(
                id=1,
                name_en="Coin",
                name_es="Moneda",
                name_de="Münze",
                name_fr="Pièce",
                description_en="Primary",
                description_es="Principal",
                description_de="Haupt",
                description_fr="Principale",
                icon_url="https://example.com/coin.png"
            )
        ]

        with patch('app.services.currencies_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB Connection error")

            # Act - should not raise exception, just log the error
            await currencies_service._sync_currencies_to_db(currencies_data)

            # Assert - if we reached here, the error was handled correctly
            assert True

    @pytest.mark.asyncio
    async def test_get_all_currencies_calls_correct_languages(
            self,
            currencies_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: verify that all languages in Constants.LANGS are called"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        await currencies_service.get_all_currencies()

        # Assert
        calls = mock_gw2_client.get_currencies.call_args_list
        assert len(calls) == len(Constants.LANGS)

        for i, lang in enumerate(Constants.LANGS):
            assert calls[i].kwargs.get('lang') == lang

    @pytest.mark.asyncio
    async def test_get_all_currencies_api_failure_no_db_data(
            self,
            currencies_service,
            mock_gw2_client,
            mock_repository
    ):
        """Test: error when the API fails and there is no data in the DB"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = Exception("API Error")
        mock_repository.get_all.return_value = []

        # Act & Assert
        with pytest.raises(RuntimeError, match="No currencies available from API or database"):
            await currencies_service.get_all_currencies()

    @pytest.mark.asyncio
    async def test_currencies_data_structure(
            self,
            currencies_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: verify the structure of the returned data"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await currencies_service.get_all_currencies()

        # Assert
        for currency in result:
            assert isinstance(currency, CurrencyDTO)
            assert hasattr(currency, 'id')
            assert hasattr(currency, 'icon_url')
            assert hasattr(currency, 'name_en')
            assert hasattr(currency, 'name_es')
            assert hasattr(currency, 'name_de')
            assert hasattr(currency, 'name_fr')
            assert hasattr(currency, 'description_en')
            assert hasattr(currency, 'description_es')
            assert hasattr(currency, 'description_de')
            assert hasattr(currency, 'description_fr')
