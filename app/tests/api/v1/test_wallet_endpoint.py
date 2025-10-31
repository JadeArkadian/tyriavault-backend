from unittest.mock import AsyncMock, patch
from uuid import UUID

import httpx
import pytest

from app.api.v1.responses.wallet_response import WalletItemResponse
from app.main import api
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

        # Mock wallet response
        mock_wallet_response = [
            WalletItemResponse(
                currency_id=1,
                amount=1234567,
                currency_name={
                    "en": "Coin",
                    "es": "Moneda",
                    "de": "Münze",
                    "fr": "Pièce"
                },
                currency_icon="https://render.guildwars2.com/file/coin.png",
                currency_description={
                    "en": "The primary currency",
                    "es": "La moneda principal",
                    "de": "Die Hauptwährung",
                    "fr": "La monnaie principale"
                }
            ),
            WalletItemResponse(
                currency_id=2,
                amount=500000,
                currency_name={
                    "en": "Karma",
                    "es": "Karma",
                    "de": "Karma",
                    "fr": "Karma"
                },
                currency_icon="https://render.guildwars2.com/file/karma.png",
                currency_description={
                    "en": "Earned by helping others",
                    "es": "Ganado ayudando a otros",
                    "de": "Verdient durch Hilfe für andere",
                    "fr": "Gagné en aidant les autres"
                }
            ),
            WalletItemResponse(
                currency_id=4,
                amount=125,
                currency_name={
                    "en": "Gems",
                    "es": "Gemas",
                    "de": "Edelsteine",
                    "fr": "Gemmes"
                },
                currency_icon="https://render.guildwars2.com/file/gems.png",
                currency_description={
                    "en": "Premium currency",
                    "es": "Moneda premium",
                    "de": "Premium-Währung",
                    "fr": "Monnaie premium"
                }
            )
        ]

        # Mock the service
        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        # Override dependencies
        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Patch get_wallet_service to return mock
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-1234"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify response is a list
            assert isinstance(json_response, list)
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
            mock_service.get_wallet.assert_called_once_with(
                UUID("12345678-1234-1234-1234-123456789abc")
            )
        finally:
            # Clean up - always clear overrides
            api.dependency_overrides.clear()

    async def test_get_wallet_empty(self):
        """Test response when wallet is empty"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-empty",
            "game_account_uuid": UUID("00000000-0000-0000-0000-000000000001"),
            "world_id": 2001
        }

        # Mock the service
        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=[])

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-empty"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert json_response == []

            # Verify service was called
            mock_service.get_wallet.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_with_zero_amounts(self):
        """Test wallet with zero amounts"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-zero",
            "game_account_uuid": UUID("11111111-1111-1111-1111-111111111111"),
            "world_id": 2001
        }

        mock_wallet_response = [
            WalletItemResponse(
                currency_id=1,
                amount=0,
                currency_name={
                    "en": "Coin",
                    "es": "Moneda",
                    "de": "Münze",
                    "fr": "Pièce"
                },
                currency_icon="https://render.guildwars2.com/file/coin.png",
                currency_description={
                    "en": "The primary currency",
                    "es": "La moneda principal",
                    "de": "Die Hauptwährung",
                    "fr": "La monnaie principale"
                }
            )
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-zero"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 1
            assert json_response[0]["amount"] == 0
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_with_large_amounts(self):
        """Test wallet with large currency amounts"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-rich",
            "game_account_uuid": UUID("99999999-9999-9999-9999-999999999999"),
            "world_id": 2001
        }

        mock_wallet_response = [
            WalletItemResponse(
                currency_id=1,
                amount=999999999,  # Very large amount
                currency_name={
                    "en": "Coin",
                    "es": "Moneda",
                    "de": "Münze",
                    "fr": "Pièce"
                },
                currency_icon="https://render.guildwars2.com/file/coin.png",
                currency_description={
                    "en": "The primary currency",
                    "es": "La moneda principal",
                    "de": "Die Hauptwährung",
                    "fr": "La monnaie principale"
                }
            )
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-rich"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert json_response[0]["amount"] == 999999999
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_with_null_icon(self):
        """Test wallet entry with null icon_url"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-noicon",
            "game_account_uuid": UUID("22222222-2222-2222-2222-222222222222"),
            "world_id": 2001
        }

        mock_wallet_response = [
            WalletItemResponse(
                currency_id=99,
                amount=1000,
                currency_name={
                    "en": "Test Currency",
                    "es": "Moneda de prueba",
                    "de": "Testwährung",
                    "fr": "Monnaie de test"
                },
                currency_icon=None,  # No icon
                currency_description={
                    "en": "Test description",
                    "es": "Descripción de prueba",
                    "de": "Testbeschreibung",
                    "fr": "Description de test"
                }
            )
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-noicon"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert json_response[0]["currency_icon"] is None
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_response_structure(self):
        """Test that response follows the expected WalletItemResponse schema"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-structure",
            "game_account_uuid": UUID("33333333-3333-3333-3333-333333333333"),
            "world_id": 2001
        }

        mock_wallet_response = [
            WalletItemResponse(
                currency_id=23,
                amount=75,
                currency_name={
                    "en": "Laurels",
                    "es": "Laureles",
                    "de": "Lorbeeren",
                    "fr": "Lauriers"
                },
                currency_icon="https://render.guildwars2.com/file/laurel.png",
                currency_description={
                    "en": "Earned for daily login rewards",
                    "es": "Obtenidos por recompensas de inicio de sesión diarias",
                    "de": "Verdient für tägliche Anmeldebelohnungen",
                    "fr": "Gagné pour les récompenses de connexion quotidiennes"
                }
            )
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-structure"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            wallet_item = json_response[0]

            # Verify required fields exist
            assert "currency_id" in wallet_item
            assert "amount" in wallet_item
            assert "currency_name" in wallet_item
            assert "currency_icon" in wallet_item
            assert "currency_description" in wallet_item

            # Verify currency_name is a dict with all languages
            assert isinstance(wallet_item["currency_name"], dict)
            assert set(wallet_item["currency_name"].keys()) == {"en", "es", "de", "fr"}

            # Verify currency_description is a dict with all languages
            assert isinstance(wallet_item["currency_description"], dict)
            assert set(wallet_item["currency_description"].keys()) == {"en", "es", "de", "fr"}

            # Verify data types
            assert isinstance(wallet_item["currency_id"], int)
            assert isinstance(wallet_item["amount"], int)
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_multiple_currencies(self):
        """Test response with multiple wallet entries"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-many",
            "game_account_uuid": UUID("44444444-4444-4444-4444-444444444444"),
            "world_id": 2001
        }

        # Create 10 different wallet entries
        mock_wallet_response = [
            WalletItemResponse(
                currency_id=i,
                amount=i * 1000,
                currency_name={
                    "en": f"Currency {i}",
                    "es": f"Moneda {i}",
                    "de": f"Währung {i}",
                    "fr": f"Monnaie {i}"
                },
                currency_icon=f"https://example.com/icon{i}.png",
                currency_description={
                    "en": f"Description {i}",
                    "es": f"Descripción {i}",
                    "de": f"Beschreibung {i}",
                    "fr": f"Description {i}"
                }
            )
            for i in range(1, 11)
        ]

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(return_value=mock_wallet_response)

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                    response = await ac.get(
                        "/api/v1/account/wallet",
                        headers={"Authorization": "Bearer test-api-key-many"}
                    )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response) == 10

            # Verify all entries have correct structure
            for i, wallet_item in enumerate(json_response, start=1):
                assert wallet_item["currency_id"] == i
                assert wallet_item["amount"] == i * 1000
                assert wallet_item["currency_name"]["en"] == f"Currency {i}"
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_service_error(self):
        """Test response when wallet service raises an exception"""
        # Arrange
        mock_api_key_data = {
            "api_key": "test-api-key-error",
            "game_account_uuid": UUID("55555555-5555-5555-5555-555555555555"),
            "world_id": 2001
        }

        mock_service = AsyncMock(spec=WalletService)
        mock_service.get_wallet = AsyncMock(
            side_effect=RuntimeError("Database connection error")
        )

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            with patch('app.api.v1.account_endpoint.get_wallet_service', return_value=mock_service):
                # Act & Assert - Exception should be raised
                async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=api),
                        base_url="http://test",
                        follow_redirects=True
                ) as ac:
                    with pytest.raises(RuntimeError, match="Database connection error"):
                        await ac.get(
                            "/api/v1/account/wallet",
                            headers={"Authorization": "Bearer test-api-key-error"}
                        )

            # Verify service was called
            mock_service.get_wallet.assert_called_once()
        finally:
            api.dependency_overrides.clear()

    async def test_get_wallet_unauthorized_without_api_key(self):
        """Test that request without API key is rejected"""
        # No dependency override - validation should fail
        try:
            # Act
            async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=api),
                    base_url="http://test"
            ) as ac:
                response = await ac.get("/api/v1/account/wallet")

            # Assert - Should return 401 or 422 (depending on validation)
            assert response.status_code in [401, 422]
        finally:
            api.dependency_overrides.clear()
