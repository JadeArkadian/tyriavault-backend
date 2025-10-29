from unittest.mock import AsyncMock

import pytest

from app.gw2.client import GW2Client
from app.services.health_service import HealthService


@pytest.mark.asyncio
class TestHealthService:
    """Tests for the HealthService"""

    async def test_check_gw2_api_status_when_api_is_up(self):
        """Test check_gw2_api_status returns True when GW2 API is responding"""
        # Arrange
        mock_gw2_client = AsyncMock(spec=GW2Client)
        mock_gw2_client.check_api_status.return_value = True
        health_service = HealthService(mock_gw2_client)

        # Act
        result = await health_service.check_gw2_api_status()

        # Assert
        assert result is True
        mock_gw2_client.check_api_status.assert_called_once()

    async def test_check_gw2_api_status_when_api_is_down(self):
        """Test check_gw2_api_status returns False when GW2 API is not responding"""
        # Arrange
        mock_gw2_client = AsyncMock(spec=GW2Client)
        mock_gw2_client.check_api_status.return_value = False
        health_service = HealthService(mock_gw2_client)

        # Act
        result = await health_service.check_gw2_api_status()

        # Assert
        assert result is False
        mock_gw2_client.check_api_status.assert_called_once()
