from unittest.mock import AsyncMock, MagicMock

import httpx
import orjson
import pytest
from pytest_mock import MockerFixture

from app.gw2.client import GW2Client, get_gw2_http_client, startup_gw2_client, shutdown_gw2_client


@pytest.mark.asyncio
class TestGW2ClientLifecycle:
    """Tests for GW2 client lifecycle management"""

    async def test_startup_gw2_client_initializes_client(self):
        """Test that startup_gw2_client creates a new AsyncClient instance"""
        await startup_gw2_client()

        client = get_gw2_http_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)

        # Cleanup
        await shutdown_gw2_client()

    async def test_get_gw2_http_client_raises_error_when_not_initialized(self):
        """Test that get_gw2_http_client raises RuntimeError when client is not initialized"""
        # Ensure client is shutdown
        await shutdown_gw2_client()

        with pytest.raises(RuntimeError) as exc:
            get_gw2_http_client()

        assert "GW2 HTTP client is not initialized" in str(exc.value)

        # Reinitialize for other tests
        await startup_gw2_client()

    async def test_shutdown_gw2_client_closes_client(self):
        """Test that shutdown_gw2_client properly closes the client"""
        await startup_gw2_client()
        client = get_gw2_http_client()
        assert client is not None

        await shutdown_gw2_client()

        # After shutdown, getting client should raise error
        with pytest.raises(RuntimeError):
            get_gw2_http_client()

        # Reinitialize for other tests
        await startup_gw2_client()

    async def test_shutdown_gw2_client_when_already_none(self):
        """Test that shutdown_gw2_client handles None client gracefully"""
        await shutdown_gw2_client()

        # Should not raise any error
        await shutdown_gw2_client()

        # Reinitialize for other tests
        await startup_gw2_client()


@pytest.mark.asyncio
class TestGW2ClientInitialization:
    """Tests for GW2Client initialization"""

    async def test_gw2client_init_with_api_key(self):
        """Test GW2Client initialization with API key"""
        client = GW2Client(api_key="test-api-key-123")

        assert client.api_key == "test-api-key-123"
        assert client.max_retries == 3
        assert client.backoff_factor == 1.5
        assert client.client is not None

    async def test_gw2client_init_without_api_key(self):
        """Test GW2Client initialization without API key"""
        client = GW2Client()

        assert client.api_key is None
        assert client.max_retries == 3
        assert client.backoff_factor == 1.5

    async def test_gw2client_init_with_custom_retries(self):
        """Test GW2Client initialization with custom retry settings"""
        client = GW2Client(api_key="test-key", max_retries=5, backoff_factor=2.0)

        assert client.max_retries == 5
        assert client.backoff_factor == 2.0

    async def test_gw2client_headers_with_api_key(self):
        """Test that _headers() returns Authorization header when API key is set"""
        client = GW2Client(api_key="my-secret-key")
        headers = client._headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer my-secret-key"

    async def test_gw2client_headers_without_api_key(self):
        """Test that _headers() returns empty dict when no API key is set"""
        client = GW2Client()
        headers = client._headers()

        assert headers == {}


@pytest.mark.asyncio
class TestGW2ClientMethods:
    """Tests for GW2Client API methods"""

    async def test_token_info_success(self, mocker: MockerFixture):
        """Test token_info method returns token information"""
        mock_response = {
            "id": "TEST-API-KEY",
            "name": "My API Key",
            "permissions": ["account", "characters"]
        }

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps(mock_response),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client(api_key="test-key")
        result = await client.token_info()

        assert result.id == "TEST-API-KEY"
        assert result.name == "My API Key"
        assert "account" in result.permissions

    async def test_token_info_requires_api_key(self):
        """Test that token_info raises ValueError when no API key is provided"""
        client = GW2Client()

        with pytest.raises(ValueError) as exc:
            await client.token_info()

        assert "requires an API key" in str(exc.value)

    async def test_get_account_success(self, mocker: MockerFixture):
        """Test get_account method returns account information"""
        mock_response = {
            "id": "account-uuid",
            "name": "Player.1234",
            "world": 2001,
            "created": "2012-08-28T00:00:00Z",
            "age": 123456,
            "guilds": [],
            "guild_leader": [],
            "access": ["GuildWars2"],
            "commander": False
        }

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps(mock_response),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client(api_key="test-key")
        result = await client.get_account()

        assert result.name == "Player.1234"
        assert result.world == 2001

    async def test_get_account_requires_api_key(self):
        """Test that get_account raises ValueError when no API key is provided"""
        client = GW2Client()

        with pytest.raises(ValueError) as exc:
            await client.get_account()

        assert "requires an API key" in str(exc.value)

    async def test_get_worlds_success(self, mocker: MockerFixture):
        """Test get_worlds method returns worlds list"""
        mock_response = [
            {"id": 1001, "name": "Anvil Rock", "population": "High"},
            {"id": 1002, "name": "Borlis Pass", "population": "Medium"}
        ]

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps(mock_response),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client()
        result = await client.get_worlds(lang="en")

        assert len(result) == 2
        assert result[0].id == 1001
        assert result[0].name == "Anvil Rock"
        assert result[1].id == 1002

    async def test_get_worlds_different_languages(self, mocker: MockerFixture):
        """Test get_worlds method with different language parameters"""
        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps([]),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client()

        await client.get_worlds(lang="es")
        await client.get_worlds(lang="de")
        await client.get_worlds(lang="fr")

        assert mock_http_client.get.call_count == 3

    async def test_get_currencies_success(self, mocker: MockerFixture):
        """Test get_currencies method returns currencies list"""
        mock_response = [
            {"id": 1, "name": "Coin", "description": "Currency", "order": 101, "icon": "https://icon.png"},
            {"id": 2, "name": "Karma", "description": "Karma points", "order": 102, "icon": "https://karma.png"}
        ]

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps(mock_response),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client()
        result = await client.get_currencies(lang="en")

        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Coin"
        assert result[1].id == 2

    async def test_get_item_success(self, mocker: MockerFixture):
        """Test get_item method returns item information"""
        mock_response = [{
            "id": 12345,
            "name": "Legendary Sword",
            "type": "Weapon"
        }]

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=200,
            content=orjson.dumps(mock_response),
            raise_for_status=MagicMock()
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client()
        result = await client.get_item_details(item_ids=[12345], lang="en")

        assert result == mock_response
        assert result[0]['id'] == 12345


@pytest.mark.asyncio
class TestGW2ClientRetryLogic:
    """Tests for GW2Client retry and error handling logic"""

    async def test_retry_on_429_rate_limit(self, mocker: MockerFixture):
        """Test that client retries on 429 rate limit error"""
        # First call returns 429, second call returns 200
        call_count = 0

        async def mock_get_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(
                    status_code=429,
                    headers={"Retry-After": "1"}
                )
            return MagicMock(
                status_code=200,
                content=orjson.dumps([{"id": 1001, "name": "Test World", "population": "High"}]),
                raise_for_status=MagicMock()
            )

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=mock_get_with_retry)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client()
        result = await client.get_worlds()

        assert len(result) == 1
        assert result[0].id == 1001
        assert call_count == 2

    async def test_retry_on_500_server_error(self, mocker: MockerFixture):
        """Test that client retries on 500 server error"""
        call_count = 0

        async def mock_get_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(
                    status_code=500,
                    raise_for_status=MagicMock()
                )
            return MagicMock(
                status_code=200,
                content=orjson.dumps([{"id": 1001, "name": "Test World", "population": "High"}]),
                raise_for_status=MagicMock()
            )

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=mock_get_with_retry)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client()
        result = await client.get_worlds()

        assert len(result) == 1
        assert result[0].id == 1001
        assert call_count == 2

    async def test_max_retries_exceeded_on_429(self, mocker: MockerFixture):
        """Test that RuntimeError is raised when max retries exceeded on 429"""
        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=MagicMock(
            status_code=429,
            headers={"Retry-After": "1"}
        ))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client(max_retries=2)

        with pytest.raises(RuntimeError) as exc:
            await client.get_worlds()

        assert "Too many retries" in str(exc.value)

    async def test_max_retries_exceeded_on_500(self, mocker: MockerFixture):
        """Test that HTTPStatusError is raised when max retries exceeded on 500"""
        mock_response = MagicMock(
            status_code=500,
            text="Internal Server Error"
        )

        def raise_for_status():
            raise httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_response)

        mock_response.raise_for_status = raise_for_status

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client(max_retries=2)

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_worlds()

    async def test_retry_on_request_error(self, mocker: MockerFixture):
        """Test that client retries on network request error"""
        call_count = 0

        async def mock_get_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("Connection failed")
            return MagicMock(
                status_code=200,
                content=orjson.dumps([{"id": 1001, "name": "Test World", "population": "High"}]),
                raise_for_status=MagicMock()
            )

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=mock_get_with_retry)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client()
        result = await client.get_worlds()

        assert len(result) == 1
        assert result[0].id == 1001
        assert call_count == 2

    async def test_max_retries_exceeded_on_request_error(self, mocker: MockerFixture):
        """Test that RuntimeError is raised when max retries exceeded on request error"""
        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client(max_retries=2)

        with pytest.raises(RuntimeError) as exc:
            await client.get_worlds()

        assert "Connection error after" in str(exc.value)
        assert "attempts" in str(exc.value)

    async def test_backoff_calculation(self, mocker: MockerFixture):
        """Test that backoff time is calculated correctly"""
        sleep_times = []

        async def mock_sleep(duration):
            sleep_times.append(duration)

        call_count = 0

        async def mock_get_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise httpx.ConnectError("Connection failed")
            return MagicMock(
                status_code=200,
                content=orjson.dumps([{"id": 1001, "name": "Test World", "population": "High"}]),
                raise_for_status=MagicMock()
            )

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=mock_get_with_retry)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock, side_effect=mock_sleep)

        client = GW2Client(backoff_factor=2.0)
        await client.get_worlds()

        # First retry: 2.0 * (2^0) = 2.0
        # Second retry: 2.0 * (2^1) = 4.0
        assert len(sleep_times) == 2
        assert sleep_times[0] == 2.0
        assert sleep_times[1] == 4.0


@pytest.mark.asyncio
class TestGW2ClientErrorHandling:
    """Tests for GW2Client error handling"""

    async def test_http_401_error(self, mocker: MockerFixture):
        """Test handling of 401 Unauthorized error"""
        mock_request = MagicMock()
        mock_response = MagicMock(status_code=401, text="Unauthorized")

        def raise_for_status():
            raise httpx.HTTPStatusError("Unauthorized", request=mock_request, response=mock_response)

        mock_response.raise_for_status = raise_for_status

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client(api_key="invalid-key")

        with pytest.raises(httpx.HTTPStatusError) as exc:
            await client.token_info()

        assert exc.value.response.status_code == 401

    async def test_http_403_error(self, mocker: MockerFixture):
        """Test handling of 403 Forbidden error"""
        mock_request = MagicMock()
        mock_response = MagicMock(status_code=403, text="Forbidden")

        def raise_for_status():
            raise httpx.HTTPStatusError("Forbidden", request=mock_request, response=mock_response)

        mock_response.raise_for_status = raise_for_status

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client(api_key="unauthorized-key")

        with pytest.raises(httpx.HTTPStatusError) as exc:
            await client.token_info()

        assert exc.value.response.status_code == 403

    async def test_http_404_error(self, mocker: MockerFixture):
        """Test handling of 404 Not Found error"""
        mock_request = MagicMock()
        mock_response = MagicMock(status_code=404, text="Not Found")

        def raise_for_status():
            raise httpx.HTTPStatusError("Not Found", request=mock_request, response=mock_response)

        mock_response.raise_for_status = raise_for_status

        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)

        client = GW2Client()

        with pytest.raises(httpx.HTTPStatusError) as exc:
            await client.get_item_details([999999])

        assert exc.value.response.status_code == 404

    async def test_connection_timeout_error(self, mocker: MockerFixture):
        """Test handling of connection timeout error"""
        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client(max_retries=1)

        with pytest.raises(RuntimeError) as exc:
            await client.get_worlds()

        assert "Connection error" in str(exc.value)

    async def test_network_error(self, mocker: MockerFixture):
        """Test handling of generic network error"""
        mock_http_client = mocker.AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.NetworkError("Network unreachable"))

        mocker.patch("app.gw2.client.get_gw2_http_client", return_value=mock_http_client)
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        client = GW2Client(max_retries=1)

        with pytest.raises(RuntimeError) as exc:
            await client.get_worlds()

        assert "Connection error" in str(exc.value)
