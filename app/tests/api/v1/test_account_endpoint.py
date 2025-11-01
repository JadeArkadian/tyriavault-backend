from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest

from app.main import api
from app.services.account_service import AccountService
from app.services.dtos.account_dto import AccountDTO
from app.services.services import validate_api_key


@pytest.mark.asyncio
class TestAccountEndpoint:
    """Tests for the /account endpoint"""

    async def test_get_account_details_success(self):
        """Test successful response from GET /account endpoint"""
        # Arrange - Mock API key validation
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        # Mock account DTO from service
        mock_account_dto = AccountDTO(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="TestAccount.1234",
            creation_date=datetime(2015, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
            fractal_level=75,
            world_id=2001,
            content_access=["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"],
            world_name_en="Anvil Rock",
            world_name_es="Roca del Yunque",
            world_name_de="Ambossfelsen",
            world_name_fr="Rocher de l'enclume"
        )

        # Mock account service
        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_dto)

        # Override dependencies
        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        # Mock get_account_service to return our mock service
        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account")

                # Assert
                assert response.status_code == 200
                json_response = response.json()

                assert json_response["uuid"] == "12345678-1234-1234-1234-123456789abc"
                assert json_response["account_name"] == "TestAccount.1234"
                assert json_response["fractal_level"] == 75
                assert json_response["content_access"] == ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]

                # Verify world name structure
                assert "world_name" in json_response
                assert json_response["world_name"]["en"] == "Anvil Rock"
                assert json_response["world_name"]["es"] == "Roca del Yunque"
                assert json_response["world_name"]["de"] == "Ambossfelsen"
                assert json_response["world_name"]["fr"] == "Rocher de l'enclume"

                # Verify creation date format
                assert "creation_date" in json_response

                # Verify service was called with correct UUID
                mock_service.get_account_details.assert_called_once_with(mock_api_key_data["game_account_uuid"])
            finally:
                api.dependency_overrides.clear()

    async def test_get_account_details_without_world(self):
        """Test response when account has no world"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": None
        }

        mock_account_dto = AccountDTO(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="TestAccount.1234",
            creation_date=datetime(2015, 6, 23, 12, 0, 0, tzinfo=timezone.utc),
            fractal_level=50,
            world_id=None,
            content_access=["PlayForFree"],
            world_name_en=None,
            world_name_es=None,
            world_name_de=None,
            world_name_fr=None
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_dto)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account")

                # Assert
                assert response.status_code == 200
                json_response = response.json()

                assert json_response["account_name"] == "TestAccount.1234"
                # World names should be None
                assert json_response["world_name"]["en"] is None
                assert json_response["world_name"]["es"] is None
            finally:
                api.dependency_overrides.clear()

    async def test_get_account_details_service_error(self):
        """Test response when service raises an exception"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(side_effect=RuntimeError("No account data available"))

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act & Assert
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test", follow_redirects=True) as ac:
                    with pytest.raises(RuntimeError, match="No account data available"):
                        await ac.get("/api/v1/account")
            finally:
                api.dependency_overrides.clear()

    async def test_get_account_details_response_structure(self):
        """Test that response follows the expected AccountInfoResponse schema"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_account_dto = AccountDTO(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="StructureTest.9999",
            creation_date=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            fractal_level=100,
            world_id=2001,
            content_access=["GuildWars2", "HeartOfThorns"],
            world_name_en="Test World",
            world_name_es="Mundo de prueba",
            world_name_de="Testwelt",
            world_name_fr="Monde de test"
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_dto)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account")

                # Assert
                assert response.status_code == 200
                json_response = response.json()

                # Verify required fields exist
                assert "uuid" in json_response
                assert "account_name" in json_response
                assert "creation_date" in json_response
                assert "fractal_level" in json_response
                assert "world_name" in json_response
                assert "content_access" in json_response

                # Verify world_name is a dict with all languages
                assert isinstance(json_response["world_name"], dict)
                assert set(json_response["world_name"].keys()) == {"en", "es", "de", "fr"}

                # Verify content_access is a list
                assert isinstance(json_response["content_access"], list)

                # Verify data types
                assert isinstance(json_response["fractal_level"], int)
                assert isinstance(json_response["account_name"], str)
            finally:
                api.dependency_overrides.clear()

    async def test_get_account_details_content_type(self):
        """Test that response has correct content type"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_account_dto = AccountDTO(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="Test.1234",
            creation_date=datetime.now(timezone.utc),
            fractal_level=1,
            world_id=None,
            content_access=[]
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_dto)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account")

                # Assert
                assert response.status_code == 200
                assert "application/json" in response.headers["content-type"]
            finally:
                api.dependency_overrides.clear()

    async def test_get_account_details_with_all_expansions(self):
        """Test account with all expansions"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_account_dto = AccountDTO(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="FullAccount.1234",
            creation_date=datetime(2012, 8, 28, 0, 0, 0, tzinfo=timezone.utc),
            fractal_level=100,
            world_id=2001,
            content_access=[
                "PlayForFree",
                "GuildWars2",
                "HeartOfThorns",
                "PathOfFire",
                "EndOfDragons",
                "SecretsOfTheObscure"
            ],
            world_name_en="Blackgate",
            world_name_es="Puerta Negra",
            world_name_de="Schwarztor",
            world_name_fr="Porte Noire"
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_dto)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account")

                # Assert
                assert response.status_code == 200
                json_response = response.json()

                assert len(json_response["content_access"]) == 6
                assert "EndOfDragons" in json_response["content_access"]
                assert "SecretsOfTheObscure" in json_response["content_access"]
                assert json_response["fractal_level"] == 100
            finally:
                api.dependency_overrides.clear()
