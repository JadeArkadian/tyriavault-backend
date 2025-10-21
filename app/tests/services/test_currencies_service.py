from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.constants import Constants
from app.database.models import Currencies
from app.services.currencies_service import CurrenciesService


@pytest.fixture
def mock_repository():
    """Mock del repositorio de currencies"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock del cliente GW2"""
    client = AsyncMock()
    return client


@pytest.fixture
def currencies_service(mock_repository, mock_gw2_client):
    """Fixture del servicio de currencies"""
    return CurrenciesService(repository=mock_repository, gw2_client=mock_gw2_client)


@pytest.fixture
def sample_api_response_en():
    """Respuesta de ejemplo de la API GW2 en inglés"""
    return [
        {
            "id": 1,
            "name": "Coin",
            "description": "The primary currency",
            "icon": "https://example.com/coin.png"
        },
        {
            "id": 2,
            "name": "Karma",
            "description": "Earned by helping others",
            "icon": "https://example.com/karma.png"
        }
    ]


@pytest.fixture
def sample_api_response_es():
    """Respuesta de ejemplo de la API GW2 en español"""
    return [
        {
            "id": 1,
            "name": "Moneda",
            "description": "La moneda principal",
            "icon": "https://example.com/coin.png"
        },
        {
            "id": 2,
            "name": "Karma",
            "description": "Ganado ayudando a otros",
            "icon": "https://example.com/karma.png"
        }
    ]


@pytest.fixture
def sample_api_response_de():
    """Respuesta de ejemplo de la API GW2 en alemán"""
    return [
        {
            "id": 1,
            "name": "Münze",
            "description": "Die Hauptwährung",
            "icon": "https://example.com/coin.png"
        },
        {
            "id": 2,
            "name": "Karma",
            "description": "Verdient durch Hilfe für andere",
            "icon": "https://example.com/karma.png"
        }
    ]


@pytest.fixture
def sample_api_response_fr():
    """Respuesta de ejemplo de la API GW2 en francés"""
    return [
        {
            "id": 1,
            "name": "Pièce",
            "description": "La monnaie principale",
            "icon": "https://example.com/coin.png"
        },
        {
            "id": 2,
            "name": "Karma",
            "description": "Gagné en aidant les autres",
            "icon": "https://example.com/karma.png"
        }
    ]


@pytest.fixture
def sample_db_currencies():
    """Currencies de ejemplo desde la base de datos"""
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
    """Test suite para CurrenciesService"""

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
        """Test: obtener currencies exitosamente desde la API"""
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
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Coin"
        assert result[0]["name_es"] == "Moneda"
        assert result[0]["name_de"] == "Münze"
        assert result[0]["name_fr"] == "Pièce"
        assert result[0]["icon_url"] == "https://example.com/coin.png"

        assert result[1]["id"] == 2
        assert result[1]["name_en"] == "Karma"

        # Verificar que se llamó a la API para cada idioma
        assert mock_gw2_client.get_currencies.call_count == 4

    @pytest.mark.asyncio
    async def test_get_all_currencies_fallback_to_db(
            self,
            currencies_service,
            mock_gw2_client,
            mock_repository,
            sample_db_currencies
    ):
        """Test: fallback a la base de datos cuando la API falla"""
        # Arrange
        mock_gw2_client.get_currencies.side_effect = Exception("API Error")
        mock_repository.get_all.return_value = sample_db_currencies

        # Act
        result = await currencies_service.get_all_currencies()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Coin"
        assert result[0]["name_es"] == "Moneda"
        assert result[1]["id"] == 2

        # Verificar que se llamó al repositorio
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
        """Test: _get_currencies_from_api combina correctamente todos los idiomas"""
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

        # Verificar que la primera currency tiene todos los idiomas
        currency = result[0]
        assert "name_en" in currency
        assert "name_es" in currency
        assert "name_de" in currency
        assert "name_fr" in currency
        assert "description_en" in currency
        assert "description_es" in currency
        assert "description_de" in currency
        assert "description_fr" in currency
        assert "icon_url" in currency

    @pytest.mark.asyncio
    async def test_get_currencies_from_db_success(
            self,
            currencies_service,
            mock_repository,
            sample_db_currencies
    ):
        """Test: obtener currencies desde la base de datos exitosamente"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_currencies

        # Act
        result = await currencies_service._get_currencies_from_db()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Coin"
        assert result[0]["name_es"] == "Moneda"
        assert result[0]["icon_url"] == "https://example.com/coin.png"

        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_currencies_from_db_empty_raises_error(
            self,
            currencies_service,
            mock_repository
    ):
        """Test: error cuando la base de datos está vacía"""
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
        """Test: error cuando el repositorio falla"""
        # Arrange
        mock_repository.get_all.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await currencies_service._get_currencies_from_db()

    @pytest.mark.asyncio
    async def test_sync_currencies_to_db_success(self, currencies_service):
        """Test: sincronización exitosa de currencies a la base de datos"""
        # Arrange
        currencies_data = [
            {
                "id": 1,
                "name_en": "Coin",
                "name_es": "Moneda",
                "icon_url": "https://example.com/coin.png"
            }
        ]

        mock_session = AsyncMock()
        mock_repo = AsyncMock()

        with patch('app.services.currencies_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch('app.services.currencies_service.CurrenciesRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Act
                await currencies_service._sync_currencies_to_db(currencies_data)

                # Assert
                mock_repo.upsert_batch.assert_called_once_with(currencies_data)

    @pytest.mark.asyncio
    async def test_sync_currencies_to_db_handles_error(self, currencies_service):
        """Test: manejo de errores durante la sincronización"""
        # Arrange
        currencies_data = [{"id": 1, "name_en": "Coin"}]

        with patch('app.services.currencies_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.side_effect = Exception("DB Connection error")

            # Act - no debe lanzar excepción, solo loggear
            await currencies_service._sync_currencies_to_db(currencies_data)

            # Assert - si llegamos aquí, el error fue manejado correctamente
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
        """Test: verificar que se llaman todos los idiomas de Constants.LANGS"""
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
        """Test: error cuando la API falla y no hay datos en la DB"""
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
        """Test: verificar la estructura de datos retornada"""
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
            assert "id" in currency
            assert "icon_url" in currency
            assert "name_en" in currency
            assert "name_es" in currency
            assert "name_de" in currency
            assert "name_fr" in currency
            assert "description_en" in currency
            assert "description_es" in currency
            assert "description_de" in currency
            assert "description_fr" in currency
