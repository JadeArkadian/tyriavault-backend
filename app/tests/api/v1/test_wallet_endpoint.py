from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest

from app.main import api
from app.services.dtos.wallet_dto import WalletItemDTO
from app.services.services import validate_api_key
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
class TestWalletEndpoint:
    """Tests for the /account/wallet endpoint"""

    async def test_get_wallet_success(self):
        """Test successful response from GET /account/wallet endpoint"""
        # Arrange - Mock API key validation
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        # Mock wallet DTOs from service
        mock_wallet_dtos = [
            WalletItemDTO(
                currency_id=1,
                amount=1234567,
                currency_name_en="Coin",
                currency_name_es="Moneda",
                currency_name_de="Münze",
                currency_name_fr="Pièce",
                currency_description_en="The primary currency",
                currency_description_es="La moneda principal",
                currency_description_de="Die Hauptwährung",
                currency_description_fr="La monnaie principale",
                currency_icon_url="https://render.guildwars2.com/file/coin.png"
            ),
            WalletItemDTO(
                currency_id=2,
                amount=500000,
                currency_name_en="Karma",
                currency_name_es="Karma",
                currency_name_de="Karma",
                currency_name_fr="Karma",
                currency_description_en="Earned by helping others",
                currency_description_es="Ganado ayudando a otros",
                currency_description_de="Verdient durch Hilfe für andere",
                currency_description_fr="Gagné en aidant les autres",
                currency_icon_url="https://render.guildwars2.com/file/karma.png"
            ),
            WalletItemDTO(
                currency_id=4,
                amount=125,
                currency_name_en="Gems",
                currency_name_es="Gemas",
                currency_name_de="Edelsteine",
                currency_name_fr="Gemmes",
                currency_description_en="Premium currency",
                currency_description_es="Moneda premium",
                currency_description_de="Premium-Währung",
                currency_description_fr="Monnaie premium",
                currency_icon_url="https://render.guildwars2.com/file/gems.png"
            )
        ]

        # Mock wallet service
        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_dtos)

        # Override dependencies
        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        # Mock get_wallet_service to return our mock service
        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account/wallet")

                # Assert
                assert response.status_code == 200
                json_response = response.json()
                assert len(json_response) == 3

                # Verify first currency (Coin)
                first_item = json_response[0]
                assert first_item["currency_id"] == 1
                assert first_item["amount"] == 1234567
                assert first_item["currency_name"]["en"] == "Coin"
                assert first_item["currency_name"]["es"] == "Moneda"
                assert first_item["currency_icon"] == "https://render.guildwars2.com/file/coin.png"
                assert first_item["currency_description"]["en"] == "The primary currency"

                # Verify second currency (Karma)
                second_item = json_response[1]
                assert second_item["currency_id"] == 2
                assert second_item["amount"] == 500000
                assert second_item["currency_name"]["en"] == "Karma"

                # Verify third currency (Gems)
                third_item = json_response[2]
                assert third_item["currency_id"] == 4
                assert third_item["amount"] == 125
                assert third_item["currency_name"]["en"] == "Gems"

                # Verify service was called with correct UUID
                mock_service.get_wallet.assert_called_once_with(mock_api_key_data["game_account_uuid"])
            finally:
                api.dependency_overrides.clear()

    async def test_get_wallet_empty(self):
        """Test response when wallet is empty"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        # Mock empty wallet
        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=[])

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account/wallet")

                # Assert
                assert response.status_code == 200
                assert response.json() == []
            finally:
                api.dependency_overrides.clear()

    async def test_get_wallet_service_error(self):
        """Test response when service raises an exception"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(side_effect=RuntimeError("Database error"))

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act & Assert
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test", follow_redirects=True) as ac:
                    with pytest.raises(RuntimeError, match="Database error"):
                        await ac.get("/api/v1/account/wallet")
            finally:
                api.dependency_overrides.clear()

    async def test_get_wallet_response_structure(self):
        """Test that response follows the expected WalletItemResponse schema"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_wallet_dtos = [
            WalletItemDTO(
                currency_id=1,
                amount=999999,
                currency_name_en="Test Currency",
                currency_name_es="Moneda de prueba",
                currency_name_de="Testwährung",
                currency_name_fr="Monnaie de test",
                currency_description_en="Test description",
                currency_description_es="Descripción de prueba",
                currency_description_de="Testbeschreibung",
                currency_description_fr="Description de test",
                currency_icon_url="https://example.com/icon.png"
            )
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_dtos)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account/wallet")

                # Assert
                assert response.status_code == 200
                json_response = response.json()

                item = json_response[0]

                # Verify required fields exist
                assert "currency_id" in item
                assert "amount" in item
                assert "currency_name" in item
                assert "currency_icon" in item
                assert "currency_description" in item

                # Verify currency_name is a dict with all languages
                assert isinstance(item["currency_name"], dict)
                assert set(item["currency_name"].keys()) == {"en", "es", "de", "fr"}

                # Verify currency_description is a dict with all languages
                assert isinstance(item["currency_description"], dict)
                assert set(item["currency_description"].keys()) == {"en", "es", "de", "fr"}

                # Verify data types
                assert isinstance(item["currency_id"], int)
                assert isinstance(item["amount"], int)
            finally:
                api.dependency_overrides.clear()

    async def test_get_wallet_multiple_currencies(self):
        """Test response with multiple currencies"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        # Create 10 different currencies
        mock_wallet_dtos = [
            WalletItemDTO(
                currency_id=i,
                amount=1000 * i,
                currency_name_en=f"Currency {i}",
                currency_name_es=f"Moneda {i}",
                currency_name_de=f"Währung {i}",
                currency_name_fr=f"Monnaie {i}",
                currency_description_en=f"Description {i}",
                currency_description_es=f"Descripción {i}",
                currency_description_de=f"Beschreibung {i}",
                currency_description_fr=f"Description {i}",
                currency_icon_url=f"https://example.com/icon{i}.png"
            )
            for i in range(1, 11)
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_dtos)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account/wallet")

                # Assert
                assert response.status_code == 200
                json_response = response.json()
                assert len(json_response) == 10

                # Verify all currencies have correct structure
                for i, item in enumerate(json_response, start=1):
                    assert item["currency_id"] == i
                    assert item["amount"] == 1000 * i
                    assert item["currency_name"]["en"] == f"Currency {i}"
            finally:
                api.dependency_overrides.clear()

    async def test_get_wallet_content_type(self):
        """Test that response has correct content type"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-1234",
            "game_account_uuid": UUID("12345678-1234-1234-1234-123456789abc"),
            "world_id": 2001
        }

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=[])

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
            try:
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get("/api/v1/account/wallet")

                # Assert
                assert response.status_code == 200
                assert "application/json" in response.headers["content-type"]
            finally:
                api.dependency_overrides.clear()
