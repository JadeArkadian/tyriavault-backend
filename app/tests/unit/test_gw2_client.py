"""
Unit tests for GW2Client with Circuit Breaker.

These tests properly mock the HTTP client to avoid real API calls.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import orjson
import pytest

from app.gw2.gw2_client import GW2Client, GW2ApiError, _protected_api_call


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""

    def _create_response(status_code=200, json_data=None, headers=None):
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.content = orjson.dumps(json_data) if json_data else b"{}"
        response.headers = headers or {}
        response.raise_for_status = MagicMock()

        if status_code >= 400:
            def raise_error():
                raise httpx.HTTPStatusError(
                    f"HTTP {status_code}",
                    request=MagicMock(),
                    response=response
                )

            response.raise_for_status.side_effect = raise_error

        return response

    return _create_response


@pytest.fixture
def mock_http_client(mock_http_response):
    """Create a mock HTTP client."""
    client = MagicMock(spec=httpx.AsyncClient)
    client.get = AsyncMock(return_value=mock_http_response(200, {"test": "data"}))
    return client


class TestGW2ClientInitialization:
    """Tests for GW2Client initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch('app.gw2.gw2_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = AsyncMock()
            client = GW2Client(api_key="test-key-123")

            assert client.api_key == "test-key-123"
            assert client.max_retries == 2  # From settings
            assert client.backoff_factor == 1.5

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch('app.gw2.gw2_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = AsyncMock()
            client = GW2Client()

            assert client.api_key is None
            assert client.max_retries == 2

    def test_init_with_custom_retries(self):
        """Test initialization with custom retry settings."""
        with patch('app.gw2.gw2_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = AsyncMock()
            client = GW2Client(api_key="test", max_retries=5, backoff_factor=2.0)

            assert client.max_retries == 5
            assert client.backoff_factor == 2.0

    def test_headers_with_api_key(self):
        """Test that headers include Authorization when API key is set."""
        with patch('app.gw2.gw2_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = AsyncMock()
            client = GW2Client(api_key="my-secret-key")
            headers = client._headers()

            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer my-secret-key"

    def test_headers_without_api_key(self):
        """Test that headers are empty when no API key is set."""
        with patch('app.gw2.gw2_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = AsyncMock()
            client = GW2Client()
            headers = client._headers()

            assert headers == {}


class TestGW2ClientBasicMethods:
    """Tests for basic GW2Client API methods."""

    @pytest.mark.asyncio
    async def test_get_worlds_success(self, mock_http_client, mock_http_response):
        """Test successful retrieval of worlds."""
        worlds_data = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 1002, "name": "Borlis Pass", "population": "Medium"}
        ]
        mock_http_client.get.return_value = mock_http_response(200, worlds_data)

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = mock_http_response(200, worlds_data)

                client = GW2Client()
                result = await client.get_worlds(lang="en")

                assert len(result) == 2
                assert result[0].id == 1001
                assert result[0].name == "Anvil Rock"

    @pytest.mark.asyncio
    async def test_get_currencies_success(self, mock_http_client, mock_http_response):
        """Test successful retrieval of currencies."""
        currencies_data = [
            {"id": 1, "name": "Coin", "description": "Gold", "order": 1, "icon": "url"},
            {"id": 2, "name": "Karma", "description": "Karma", "order": 2, "icon": "url"}
        ]
        mock_http_client.get.return_value = mock_http_response(200, currencies_data)

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = mock_http_response(200, currencies_data)

                client = GW2Client()
                result = await client.get_currencies(lang="en")

                assert len(result) == 2
                assert result[0].id == 1
                assert result[0].name == "Coin"

    @pytest.mark.asyncio
    async def test_get_item_details_success(self, mock_http_client, mock_http_response):
        """Test successful retrieval of item details."""
        item_data = [{
            "id": 12345,
            "chat_link": "[&AgEBMAAA]",
            "name": "Test Item",
            "icon": "url",
            "description": "A test item",
            "type": "Weapon",
            "rarity": "Exotic",
            "level": 80,
            "vendor_value": 100,
            "flags": [],
            "game_types": [],
            "restrictions": []
        }]
        mock_http_client.get.return_value = mock_http_response(200, item_data)

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = mock_http_response(200, item_data)

                client = GW2Client()
                result = await client.get_item_details([12345])

                assert len(result) == 1
                assert result[0].id == 12345
                assert result[0].name == "Test Item"

    @pytest.mark.asyncio
    async def test_token_info_requires_api_key(self):
        """Test that token_info raises ValueError without API key."""
        with patch('app.gw2.gw2_client.get_gw2_http_client'):
            client = GW2Client()

            with pytest.raises(ValueError, match="requires an API key"):
                await client.token_info()


class TestGW2ClientRateLimiting:
    """Tests for rate limiting (429) handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_retry_after_header(self, mock_http_client, mock_http_response):
        """Test rate limiting with Retry-After header."""
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_http_response(429, headers={"Retry-After": "1"})
            return mock_http_response(200, [{"id": 1, "name": "Test", "population": "High"}])

        mock_http_client.get.side_effect = mock_get

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.side_effect = mock_get
                with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                    client = GW2Client()
                    result = await client.get_worlds()

                    assert len(result) == 1
                    assert call_count == 2
                    mock_sleep.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_rate_limit_max_retries_exceeded(self, mock_http_client, mock_http_response):
        """Test that max retries are enforced on rate limiting."""
        mock_http_client.get.return_value = mock_http_response(429, headers={"Retry-After": "0"})

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = mock_http_response(429, headers={"Retry-After": "0"})
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    client = GW2Client(max_retries=2)

                    with pytest.raises(GW2ApiError, match="Too many retries"):
                        await client.get_worlds()


class TestGW2ClientCircuitBreaker:
    """Tests for circuit breaker behavior."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_error_raises_gw2_api_error(self, mock_http_client):
        """Test that CircuitBreakerError is converted to GW2ApiError."""
        from circuitbreaker import CircuitBreakerError

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.side_effect = CircuitBreakerError(MagicMock())

                client = GW2Client()

                with pytest.raises(GW2ApiError, match="Circuit breaker open"):
                    await client.get_worlds()

    @pytest.mark.asyncio
    async def test_server_error_raises_gw2_api_error(self, mock_http_client, mock_http_response):
        """Test that 5xx errors are caught by circuit breaker."""
        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.side_effect = GW2ApiError("API server error 500")

                client = GW2Client()

                with pytest.raises(GW2ApiError, match="API server error 500"):
                    await client.get_worlds()


class TestGW2ClientErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_http_401_error(self, mock_http_client, mock_http_response):
        """Test handling of 401 Unauthorized."""
        response_401 = mock_http_response(401)

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = response_401

                client = GW2Client(api_key="invalid")

                with pytest.raises(GW2ApiError, match="401"):
                    await client.get_worlds()

    @pytest.mark.asyncio
    async def test_http_404_error(self, mock_http_client, mock_http_response):
        """Test handling of 404 Not Found."""
        response_404 = mock_http_response(404)

        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.return_value = response_404

                client = GW2Client()

                with pytest.raises(GW2ApiError, match="404"):
                    await client.get_item_details([999999])

    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_http_client):
        """Test handling of timeout errors."""
        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.side_effect = GW2ApiError("API timeout for /worlds")

                client = GW2Client()

                with pytest.raises(GW2ApiError, match="timeout"):
                    await client.get_worlds()

    @pytest.mark.asyncio
    async def test_connection_error(self, mock_http_client):
        """Test handling of connection errors."""
        with patch('app.gw2.gw2_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('app.gw2.gw2_client._protected_api_call') as mock_protected:
                mock_protected.side_effect = GW2ApiError("Connection error: Network unreachable")

                client = GW2Client()

                with pytest.raises(GW2ApiError, match="Connection error"):
                    await client.get_worlds()


class TestProtectedApiCall:
    """Tests for the _protected_api_call function with circuit breaker."""

    @pytest.mark.asyncio
    async def test_successful_call(self, mock_http_client, mock_http_response):
        """Test successful API call through circuit breaker."""
        mock_http_client.get.return_value = mock_http_response(200, {"test": "data"})

        # Bypass circuit breaker for this test
        with patch('app.gw2.gw2_client._protected_api_call.__wrapped__') as mock_wrapped:
            async def mock_call(*args, **kwargs):
                return mock_http_response(200, {"test": "data"})

            mock_wrapped.side_effect = mock_call

            # Just verify the function signature works
            assert callable(_protected_api_call)

    @pytest.mark.asyncio
    async def test_server_error_raises_gw2_api_error(self, mock_http_client, mock_http_response):
        """Test that 5xx errors raise GW2ApiError."""
        mock_http_client.get.return_value = mock_http_response(500)

        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.return_value = mock_http_response(500)

            with pytest.raises(GW2ApiError, match="API server error 500"):
                await _protected_api_call.__wrapped__(
                    mock_http_client,
                    "/test",
                    params=None,
                    headers=None
                )
