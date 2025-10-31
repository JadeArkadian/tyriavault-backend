from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.models import Dyes
from app.gw2.responses import GW2ApiColor, MaterialColor
from app.services.dyes_service import DyesService


def create_color(color_id: int, name: str, rgb: tuple[int, int, int]) -> GW2ApiColor:
    """Helper function to create a Color object for testing."""
    material = MaterialColor(
        brightness=0,
        contrast=1.0,
        hue=0,
        saturation=0.0,
        lightness=1.0,
        rgb=list(rgb)
    )
    return GW2ApiColor(
        id=color_id,
        name=name,
        base_rgb=list(rgb),
        cloth=material,
        leather=material,
        metal=material,
        fur=material,
        item=None,
        categories=[]
    )


@pytest.fixture
def mock_repository():
    """Mock repository for dyes"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_gw2_client():
    """Mock GW2 client"""
    client = AsyncMock()
    return client


@pytest.fixture
def dyes_service(mock_repository, mock_gw2_client):
    """Fixture for dyes service"""
    return DyesService(repository=mock_repository, gw2_client=mock_gw2_client)


@pytest.fixture
def sample_api_response_en():
    """Sample response from GW2 API in English"""
    return [
        create_color(1, "Black", (0, 0, 0)),
        create_color(2, "White", (255, 255, 255))
    ]


@pytest.fixture
def sample_api_response_es():
    """Sample response from GW2 API in Spanish"""
    return [
        create_color(1, "Negro", (0, 0, 0)),
        create_color(2, "Blanco", (255, 255, 255))
    ]


@pytest.fixture
def sample_api_response_de():
    """Sample response from GW2 API in German"""
    return [
        create_color(1, "Schwarz", (0, 0, 0)),
        create_color(2, "Weiß", (255, 255, 255))
    ]


@pytest.fixture
def sample_api_response_fr():
    """Sample response from GW2 API in French"""
    return [
        create_color(1, "Noir", (0, 0, 0)),
        create_color(2, "Blanc", (255, 255, 255))
    ]


@pytest.fixture
def sample_db_dyes():
    """Sample dyes from the database"""
    dye1 = MagicMock(spec=Dyes)
    dye1.id = 1
    dye1.name_en = "Black"
    dye1.name_es = "Negro"
    dye1.name_de = "Schwarz"
    dye1.name_fr = "Noir"
    dye1.color = "#000000"

    dye2 = MagicMock(spec=Dyes)
    dye2.id = 2
    dye2.name_en = "White"
    dye2.name_es = "Blanco"
    dye2.name_de = "Weiß"
    dye2.name_fr = "Blanc"
    dye2.color = "#ffffff"

    return [dye1, dye2]


class TestDyesService:
    """Test suite for DyesService"""

    @pytest.mark.asyncio
    async def test_get_all_dyes_success_from_api(
            self,
            dyes_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: successfully obtain dyes from the API"""
        # Arrange
        mock_gw2_client.get_colors.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        with patch.object(dyes_service, '_sync_dyes_to_db', new_callable=AsyncMock):
            result = await dyes_service.get_all_dyes()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Black"
        assert result[0]["name_es"] == "Negro"
        assert result[0]["name_de"] == "Schwarz"
        assert result[0]["name_fr"] == "Noir"
        assert result[0]["color"] == "#000000"

        assert result[1]["id"] == 2
        assert result[1]["name_en"] == "White"
        assert result[1]["name_es"] == "Blanco"
        assert result[1]["name_de"] == "Weiß"
        assert result[1]["name_fr"] == "Blanc"
        assert result[1]["color"] == "#ffffff"

        # Verify that the API was called for each language
        assert mock_gw2_client.get_colors.call_count == 4

    @pytest.mark.asyncio
    async def test_get_all_dyes_fallback_to_db(
            self,
            dyes_service,
            mock_gw2_client,
            mock_repository,
            sample_db_dyes
    ):
        """Test: fallback to the database when the API fails"""
        # Arrange
        mock_gw2_client.get_colors.side_effect = Exception("API Error")
        mock_repository.get_all.return_value = sample_db_dyes

        # Act
        result = await dyes_service.get_all_dyes()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Black"
        assert result[0]["name_es"] == "Negro"
        assert result[0]["color"] == "#000000"

        assert result[1]["id"] == 2
        assert result[1]["name_en"] == "White"

        # Verify that the repository was called
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dyes_from_api_combines_languages(
            self,
            dyes_service,
            mock_gw2_client,
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
    ):
        """Test: _get_dyes_from_api correctly combines data from all languages"""
        # Arrange
        mock_gw2_client.get_colors.side_effect = [
            sample_api_response_en,
            sample_api_response_es,
            sample_api_response_de,
            sample_api_response_fr
        ]

        # Act
        result = await dyes_service._get_dyes_from_api()

        # Assert
        assert len(result) == 2

        # Verify first dye has all language fields
        first_dye = result[0]
        assert "name_en" in first_dye
        assert "name_es" in first_dye
        assert "name_de" in first_dye
        assert "name_fr" in first_dye
        assert "color" in first_dye
        assert "id" in first_dye

    @pytest.mark.asyncio
    async def test_get_dyes_from_db_success(
            self,
            dyes_service,
            mock_repository,
            sample_db_dyes
    ):
        """Test: successfully retrieve dyes from database"""
        # Arrange
        mock_repository.get_all.return_value = sample_db_dyes

        # Act
        result = await dyes_service._get_dyes_from_db()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "Black"
        assert result[0]["color"] == "#000000"
        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dyes_from_db_empty_raises_error(
            self,
            dyes_service,
            mock_repository
    ):
        """Test: raise error when database returns empty list"""
        # Arrange
        mock_repository.get_all.return_value = []

        # Act & Assert
        with pytest.raises(RuntimeError, match="No dyes available from API or database"):
            await dyes_service._get_dyes_from_db()

    @pytest.mark.asyncio
    async def test_get_dyes_from_db_repository_error(
            self,
            dyes_service,
            mock_repository
    ):
        """Test: raise error when repository fails"""
        # Arrange
        mock_repository.get_all.side_effect = Exception("Database connection error")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await dyes_service._get_dyes_from_db()

    @pytest.mark.asyncio
    async def test_sync_dyes_to_db_success(
            self,
            dyes_service
    ):
        """Test: successfully sync dyes to database"""
        # Arrange
        dyes_data = [
            {"id": 1, "name_en": "Black", "name_es": "Negro", "name_de": "Schwarz", "name_fr": "Noir", "color": "#000000"},
            {"id": 2, "name_en": "White", "name_es": "Blanco", "name_de": "Weiß", "name_fr": "Blanc", "color": "#ffffff"}
        ]

        mock_session = AsyncMock()
        mock_dyes_repo = AsyncMock()

        # Act
        with patch('app.services.dyes_service.async_session_maker') as mock_session_maker:
            mock_session_maker.return_value.__aenter__.return_value = mock_session
            with patch('app.services.dyes_service.DyesRepository') as mock_repo_class:
                mock_repo_class.return_value = mock_dyes_repo

                await dyes_service._sync_dyes_to_db(dyes_data)

        # Assert
        mock_dyes_repo.upsert_batch.assert_called_once_with(dyes_data)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_dyes_to_db_handles_error(
            self,
            dyes_service
    ):
        """Test: handle errors during database sync gracefully"""
        # Arrange
        dyes_data = [{"id": 1, "name_en": "Black", "color": "#000000"}]

        with patch('app.services.dyes_service.async_session_maker') as mock_session_maker:
            mock_session_maker.side_effect = Exception("Database connection error")

            # Act & Assert - should not raise exception
            await dyes_service._sync_dyes_to_db(dyes_data)

            # The method should log the error but not raise it
            # (background tasks should not crash the main request)

    @pytest.mark.asyncio
    async def test_get_all_dyes_calls_correct_languages(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: verify get_all_dyes calls API with all supported languages"""
        # Arrange
        mock_gw2_client.get_colors.return_value = []

        # Act
        with patch.object(dyes_service, '_sync_dyes_to_db', new_callable=AsyncMock):
            await dyes_service.get_all_dyes()

        # Assert - should be called 4 times (en, es, de, fr)
        assert mock_gw2_client.get_colors.call_count == 4

        # Verify the languages called
        call_args_list = mock_gw2_client.get_colors.call_args_list
        languages_called = [call.kwargs['lang'] for call in call_args_list]
        assert set(languages_called) == {'en', 'es', 'de', 'fr'}

    @pytest.mark.asyncio
    async def test_get_all_dyes_api_failure_no_db_data(
            self,
            dyes_service,
            mock_gw2_client,
            mock_repository
    ):
        """Test: raise error when both API and database fail"""
        # Arrange
        mock_gw2_client.get_colors.side_effect = Exception("API Error")
        mock_repository.get_all.return_value = []

        # Act & Assert
        with pytest.raises(RuntimeError, match="No dyes available from API or database"):
            await dyes_service.get_all_dyes()

    @pytest.mark.asyncio
    async def test_dyes_data_structure(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: verify that returned dyes have correct structure"""
        # Arrange
        api_response = [create_color(99, "Test Dye", (123, 45, 67))]
        mock_gw2_client.get_colors.side_effect = [api_response, api_response, api_response, api_response]

        # Act
        with patch.object(dyes_service, '_sync_dyes_to_db', new_callable=AsyncMock):
            result = await dyes_service.get_all_dyes()

        # Assert
        assert len(result) == 1
        dye = result[0]

        # Verify all required fields are present
        assert "id" in dye
        assert "name_en" in dye
        assert "name_es" in dye
        assert "name_de" in dye
        assert "name_fr" in dye
        assert "color" in dye

        # Verify correct hex color conversion
        assert dye["color"] == "#7b2d43"

    @pytest.mark.asyncio
    async def test_get_dyes_from_api_with_different_rgb_values(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: correctly convert different RGB values to hex"""
        # Arrange
        api_response_en = [
            create_color(1, "Red", (255, 0, 0)),
            create_color(2, "Green", (0, 255, 0)),
            create_color(3, "Blue", (0, 0, 255))
        ]
        api_response_other = [
            create_color(1, "Color1", (255, 0, 0)),
            create_color(2, "Color2", (0, 255, 0)),
            create_color(3, "Color3", (0, 0, 255))
        ]

        mock_gw2_client.get_colors.side_effect = [
            api_response_en,
            api_response_other,
            api_response_other,
            api_response_other
        ]

        # Act
        result = await dyes_service._get_dyes_from_api()

        # Assert
        assert len(result) == 3
        assert result[0]["color"] == "#ff0000"  # Red
        assert result[1]["color"] == "#00ff00"  # Green
        assert result[2]["color"] == "#0000ff"  # Blue

    @pytest.mark.asyncio
    async def test_get_all_dyes_with_single_dye(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: handle API response with single dye"""
        # Arrange
        single_dye = [create_color(1, "Only Dye", (128, 128, 128))]
        mock_gw2_client.get_colors.side_effect = [single_dye, single_dye, single_dye, single_dye]

        # Act
        with patch.object(dyes_service, '_sync_dyes_to_db', new_callable=AsyncMock):
            result = await dyes_service.get_all_dyes()

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["color"] == "#808080"

    @pytest.mark.asyncio
    async def test_get_all_dyes_with_many_dyes(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: handle API response with many dyes"""
        # Arrange
        many_dyes = [
            create_color(i, f"Dye {i}", (i % 256, (i * 2) % 256, (i * 3) % 256))
            for i in range(1, 51)  # 50 dyes
        ]
        mock_gw2_client.get_colors.side_effect = [many_dyes, many_dyes, many_dyes, many_dyes]

        # Act
        with patch.object(dyes_service, '_sync_dyes_to_db', new_callable=AsyncMock):
            result = await dyes_service.get_all_dyes()

        # Assert
        assert len(result) == 50

    @pytest.mark.asyncio
    async def test_get_dyes_from_db_converts_orm_to_dict(
            self,
            dyes_service,
            mock_repository
    ):
        """Test: verify ORM objects are correctly converted to dictionaries"""
        # Arrange
        dye = MagicMock(spec=Dyes)
        dye.id = 123
        dye.name_en = "Test Dye"
        dye.name_es = "Tinte de prueba"
        dye.name_de = "Testfarbe"
        dye.name_fr = "Teinture test"
        dye.color = "#abcdef"

        mock_repository.get_all.return_value = [dye]

        # Act
        result = await dyes_service._get_dyes_from_db()

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["id"] == 123
        assert result[0]["name_en"] == "Test Dye"
        assert result[0]["name_es"] == "Tinte de prueba"
        assert result[0]["name_de"] == "Testfarbe"
        assert result[0]["name_fr"] == "Teinture test"
        assert result[0]["color"] == "#abcdef"

    @pytest.mark.asyncio
    async def test_get_dyes_from_api_deduplicates_by_id(
            self,
            dyes_service,
            mock_gw2_client
    ):
        """Test: verify dyes are deduplicated by ID when combining languages"""
        # Arrange - Each language returns the same dye IDs
        dye_en = [create_color(1, "English Name", (100, 100, 100))]
        dye_es = [create_color(1, "Spanish Name", (100, 100, 100))]
        dye_de = [create_color(1, "German Name", (100, 100, 100))]
        dye_fr = [create_color(1, "French Name", (100, 100, 100))]

        mock_gw2_client.get_colors.side_effect = [dye_en, dye_es, dye_de, dye_fr]

        # Act
        result = await dyes_service._get_dyes_from_api()

        # Assert - Should only have 1 dye, not 4
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name_en"] == "English Name"
        assert result[0]["name_es"] == "Spanish Name"
        assert result[0]["name_de"] == "German Name"
        assert result[0]["name_fr"] == "French Name"
