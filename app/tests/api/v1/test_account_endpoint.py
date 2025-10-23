from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest

from app.api.v1.responses.account_response import AccountInfoResponse
from app.main import api
from app.services.account_service import AccountService
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

        # Mock account response
        mock_account_response = AccountInfoResponse(
            uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            account_name="TestAccount.1234",
            creation_date=datetime(2015, 6, 16, 4, 31, 0, tzinfo=timezone.utc),
            fractal_level=75,
            world_name={
                "en": "Anvil Rock",
                "es": "Roca del Yunque",
                "de": "Ambossfelsen",
                "fr": "Rocher de l'enclume"
            },
            content_access=["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]
        )

        # Mock the service
        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_response)

        # Override dependencies
        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Patch get_account_service to return mock
            with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account",
                        headers={"Authorization": "Bearer test-api-key-1234"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify response structure
            assert json_response["uuid"] == "12345678-1234-1234-1234-123456789abc"
            assert json_response["account_name"] == "TestAccount.1234"
            assert json_response["fractal_level"] == 75
            assert json_response["content_access"] == ["PlayForFree", "GuildWars2", "HeartOfThorns", "PathOfFire"]

            # Verify world_name translations
            assert json_response["world_name"]["en"] == "Anvil Rock"
            assert json_response["world_name"]["es"] == "Roca del Yunque"
            assert json_response["world_name"]["de"] == "Ambossfelsen"
            assert json_response["world_name"]["fr"] == "Rocher de l'enclume"

            # Verify creation_date is present
            assert "creation_date" in json_response

            # Verify service was called with correct UUID
            mock_service.get_account_details.assert_called_once_with(
                UUID("12345678-1234-1234-1234-123456789abc")
            )
        finally:
            # Clean up - always clear overrides
            api.dependency_overrides.clear()

    async def test_get_account_details_without_world(self):
        """Test account response when world information is not available"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-5678",
            "game_account_uuid": UUID("87654321-4321-4321-4321-cba987654321"),
            "world_id": None
        }

        mock_account_response = AccountInfoResponse(
            uuid=UUID("87654321-4321-4321-4321-cba987654321"),
            account_name="NoWorldAccount.5678",
            creation_date=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            fractal_level=1,
            world_name={
                "en": None,
                "es": None,
                "de": None,
                "fr": None
            },
            content_access=["PlayForFree"]
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account",
                        headers={"Authorization": "Bearer test-api-key-5678"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["uuid"] == "87654321-4321-4321-4321-cba987654321"
            assert json_response["account_name"] == "NoWorldAccount.5678"
            assert json_response["world_name"]["en"] is None
            assert json_response["world_name"]["es"] is None
            assert json_response["world_name"]["de"] is None
            assert json_response["world_name"]["fr"] is None

            mock_service.get_account_details.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_account_details_service_error(self):
        """Test response when account service raises an exception"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-error",
            "game_account_uuid": UUID("00000000-0000-0000-0000-000000000000"),
            "world_id": 2001
        }

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(
            side_effect=RuntimeError("No account data available from API or database")
        )

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
                # Act & Assert - Exception should be raised
                async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=api),
                        base_url="http://test",
                        follow_redirects=True
                ) as ac:
                    with pytest.raises(RuntimeError, match="No account data available from API or database"):
                        await ac.get(
                            "/api/v1/account",
                            headers={"Authorization": "Bearer test-api-key-error"}
                        )

            # Verify service was called
            mock_service.get_account_details.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_account_details_with_high_fractal_level(self):
        """Test account with high fractal level"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-pro",
            "game_account_uuid": UUID("aaaabbbb-cccc-dddd-eeee-ffff00001111"),
            "world_id": 2001
        }

        mock_account_response = AccountInfoResponse(
            uuid=UUID("aaaabbbb-cccc-dddd-eeee-ffff00001111"),
            account_name="ProPlayer.9999",
            creation_date=datetime(2012, 8, 28, 0, 0, 0, tzinfo=timezone.utc),
            fractal_level=100,
            world_name={
                "en": "Blackgate",
                "es": "Puerta Negra",
                "de": "Schwarzes Tor",
                "fr": "Porte noire"
            },
            content_access=[
                "PlayForFree",
                "GuildWars2",
                "HeartOfThorns",
                "PathOfFire",
                "EndOfDragons"
            ]
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account",
                        headers={"Authorization": "Bearer test-api-key-pro"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["fractal_level"] == 100
            assert len(json_response["content_access"]) == 5
            assert "EndOfDragons" in json_response["content_access"]
            assert json_response["world_name"]["en"] == "Blackgate"

            mock_service.get_account_details.assert_called_once_with(
                UUID("aaaabbbb-cccc-dddd-eeee-ffff00001111")
            )
        finally:
            api.dependency_overrides.clear()

    async def test_get_account_details_response_structure(self):
        """Test that response follows the expected AccountInfoResponse schema"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-schema",
            "game_account_uuid": UUID("11112222-3333-4444-5555-666677778888"),
            "world_id": 1001
        }

        mock_account_response = AccountInfoResponse(
            uuid=UUID("11112222-3333-4444-5555-666677778888"),
            account_name="SchemaTest.1111",
            creation_date=datetime(2018, 5, 10, 12, 30, 0, tzinfo=timezone.utc),
            fractal_level=50,
            world_name={
                "en": "Fissure of Woe",
                "es": "Fisura del Infortunio",
                "de": "Kluft des Leids",
                "fr": "Fissure du malheur"
            },
            content_access=["GuildWars2", "PathOfFire"]
        )

        mock_service = AsyncMock(spec=AccountService)
        mock_service.get_account_details = AsyncMock(return_value=mock_account_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_account_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account",
                        headers={"Authorization": "Bearer test-api-key-schema"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify all required fields exist
            assert "uuid" in json_response
            assert "account_name" in json_response
            assert "creation_date" in json_response
            assert "fractal_level" in json_response
            assert "world_name" in json_response
            assert "content_access" in json_response

            # Verify world_name structure
            assert isinstance(json_response["world_name"], dict)
            assert set(json_response["world_name"].keys()) == {"en", "es", "de", "fr"}

            # Verify content_access is a list
            assert isinstance(json_response["content_access"], list)

            # Verify fractal_level is an integer
            assert isinstance(json_response["fractal_level"], int)
        finally:
            api.dependency_overrides.clear()
