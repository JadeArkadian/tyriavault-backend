from unittest.mock import AsyncMock

import httpx
import pytest

from app.main import api
from app.services.apikey_service import ApiKeyService
from app.services.services import get_api_key_service, validate_api_key


@pytest.mark.asyncio
class TestCommonEndpoint:
    """Tests for the /common endpoint"""

    async def test_status_endpoint(self):
        """Test the health check endpoint returns alive"""
        # Act
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/common/status")

        # Assert
        assert response.status_code == 200
        assert response.text == "alive"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    async def test_tokeninfo_success(self):
        """Test successful tokeninfo response with valid API key"""
        # Arrange - Mock validate_api_key dependency
        mock_api_key_data = {
            "id": "test-api-key-123",
            "permissions": ["account", "characters", "inventories"],
            "name": "Test Key"
        }

        # Override the validate_api_key dependency
        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "Bearer test-api-key-123"}
                )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify response structure
            assert "permissions" in json_response
            assert isinstance(json_response["permissions"], list)
            assert json_response["permissions"] == ["account", "characters", "inventories"]
        finally:
            api.dependency_overrides.clear()

    async def test_tokeninfo_empty_permissions(self):
        """Test tokeninfo response when API key has no permissions"""
        # Arrange
        mock_api_key_data = {
            "id": "test-api-key-empty",
            "permissions": [],
            "name": "Empty Key"
        }

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "Bearer test-api-key-empty"}
                )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["permissions"] == []
        finally:
            api.dependency_overrides.clear()

    async def test_tokeninfo_missing_authorization_header(self):
        """Test tokeninfo endpoint without Authorization header"""
        # Act
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
            response = await ac.get("/api/v1/common/tokeninfo")

        # Assert
        assert response.status_code == 422  # Unprocessable Entity - missing required header

    async def test_tokeninfo_invalid_bearer_format(self):
        """Test tokeninfo with invalid Bearer token format"""
        # Arrange - Mock service but it won't be called
        mock_service = AsyncMock(spec=ApiKeyService)
        api.dependency_overrides[get_api_key_service] = lambda: mock_service

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "InvalidFormat token123"}
                )

            # Assert
            assert response.status_code == 400
            json_response = response.json()
            assert "detail" in json_response
            assert "Invalid authorization header format" in json_response["detail"]
        finally:
            api.dependency_overrides.clear()

    async def test_tokeninfo_invalid_api_key(self):
        """Test tokeninfo with invalid API key that fails validation"""

        # Arrange - Mock validate_api_key to raise an exception
        async def mock_validate_raises():
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid API key: Key not found")

        api.dependency_overrides[validate_api_key] = mock_validate_raises

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "Bearer invalid-key-123"}
                )

            # Assert
            assert response.status_code == 401
            json_response = response.json()
            assert "detail" in json_response
            assert "Invalid API key" in json_response["detail"]
        finally:
            api.dependency_overrides.clear()

    async def test_tokeninfo_all_permissions(self):
        """Test tokeninfo with API key that has all permissions"""
        # Arrange
        mock_api_key_data = {
            "id": "test-api-key-full",
            "permissions": [
                "account",
                "builds",
                "characters",
                "guilds",
                "inventories",
                "progression",
                "pvp",
                "tradingpost",
                "unlocks",
                "wallet"
            ],
            "name": "Full Access Key"
        }

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "Bearer test-api-key-full"}
                )

            # Assert
            assert response.status_code == 200
            json_response = response.json()
            assert len(json_response["permissions"]) == 10
            assert "account" in json_response["permissions"]
            assert "wallet" in json_response["permissions"]
        finally:
            api.dependency_overrides.clear()

    async def test_tokeninfo_response_structure(self):
        """Test that tokeninfo response follows the TokenInfoResponse schema"""
        # Arrange
        mock_api_key_data = {
            "id": "test-api-key-schema",
            "permissions": ["account", "characters"],
            "name": "Schema Test Key"
        }

        api.dependency_overrides[validate_api_key] = lambda: mock_api_key_data

        try:
            # Act
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as ac:
                response = await ac.get(
                    "/api/v1/common/tokeninfo",
                    headers={"Authorization": "Bearer test-api-key-schema"}
                )

            # Assert
            assert response.status_code == 200
            json_response = response.json()

            # Verify required fields exist
            assert "permissions" in json_response

            # Verify permissions is a list
            assert isinstance(json_response["permissions"], list)

            # Verify all permissions are strings
            for permission in json_response["permissions"]:
                assert isinstance(permission, str)
        finally:
            api.dependency_overrides.clear()
