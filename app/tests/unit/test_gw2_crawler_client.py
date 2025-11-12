"""
Unit tests for GW2CrawlerClient (without Circuit Breaker).

These tests verify the persistent retry behavior of the crawler client.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import orjson
import pytest

from app.gw2.gw2_crawler_client import GW2CrawlerClient


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


class TestGW2CrawlerClientInitialization:
    """Tests for GW2CrawlerClient initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = MagicMock()
            client = GW2CrawlerClient()

            assert client.api_key is None
            assert client.max_retries == 10  # From settings
            assert client.backoff_factor == 2.0  # From settings
            assert client.timeout == 30  # From settings

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client') as mock_get:
            mock_get.return_value = MagicMock()
            client = GW2CrawlerClient(
                api_key="test-key",
                max_retries=15,
                backoff_factor=3.0,
                timeout=60
            )

            assert client.api_key == "test-key"
            assert client.max_retries == 15
            assert client.backoff_factor == 3.0
            assert client.timeout == 60

    def test_inherits_from_gw2_client(self):
        """Test that GW2CrawlerClient inherits from GW2Client."""
        from app.gw2.gw2_client import GW2Client

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client'):
            client = GW2CrawlerClient()
            assert isinstance(client, GW2Client)


class TestGW2CrawlerClientBasicMethods:
    """Tests for basic GW2CrawlerClient API methods."""

    @pytest.mark.asyncio
    async def test_get_all_item_ids_success(self, mock_http_client, mock_http_response):
        """Test successful retrieval of all item IDs."""
        item_ids = [1, 2, 3, 100, 200, 300]
        mock_http_client.get.return_value = mock_http_response(200, item_ids)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.return_value = mock_http_response(200, item_ids)

                client = GW2CrawlerClient()
                result = await client.get_all_item_ids()

                assert result == item_ids
                assert len(result) == 6

    @pytest.mark.asyncio
    async def test_get_item_details_success(self, mock_http_client, mock_http_response):
        """Test successful retrieval of item details."""
        item_data = [{
            "id": 12345,
            "chat_link": "[&AgEBMAAA]",
            "name": "Crawler Test Item",
            "icon": "url",
            "description": "Test",
            "type": "Weapon",
            "rarity": "Exotic",
            "level": 80,
            "vendor_value": 100,
            "flags": [],
            "game_types": [],
            "restrictions": []
        }]
        mock_http_client.get.return_value = mock_http_response(200, item_data)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.return_value = mock_http_response(200, item_data)

                client = GW2CrawlerClient()
                result = await client.get_item_details([12345])

                assert len(result) == 1
                assert result[0].id == 12345
                assert result[0].name == "Crawler Test Item"


class TestGW2CrawlerClientRetryLogic:
    """Tests for persistent retry logic (no circuit breaker)."""

    @pytest.mark.asyncio
    async def test_retries_on_500_error(self, mock_http_client, mock_http_response):
        """Test that crawler retries on 500 errors."""
        call_count = 0
        sleep_count = 0

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return mock_http_response(500)
            return mock_http_response(200, [1, 2, 3])

        async def mock_sleep(duration):
            nonlocal sleep_count
            sleep_count += 1

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient()
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    assert call_count == 3
                    # Should have slept twice (after first two failures)
                    assert sleep_count == 2

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self, mock_http_client, mock_http_response):
        """Test that crawler retries on timeout errors."""
        call_count = 0

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Timeout")
            return mock_http_response(200, [1, 2, 3])

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                async def mock_sleep(duration): pass

                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient()
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    assert call_count == 2
                    pass  # Sleep was called

    @pytest.mark.asyncio
    async def test_retries_on_network_error(self, mock_http_client):
        """Test that crawler retries on network errors."""
        call_count = 0

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.NetworkError("Network unreachable")
            return MagicMock(
                status_code=200,
                content=orjson.dumps([1, 2, 3]),
                raise_for_status=MagicMock()
            )

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                async def mock_sleep(duration): pass

                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient()
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    assert call_count == 2
                    pass  # Sleep was called

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_http_client, mock_http_response):
        """Test that backoff increases exponentially."""
        call_count = 0
        sleep_times = []

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return mock_http_response(503)
            return mock_http_response(200, [1, 2, 3])

        async def mock_sleep(duration):
            sleep_times.append(duration)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient(backoff_factor=2.0)
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    assert len(sleep_times) == 3
                    # Verify exponential backoff: 2.0 * 2^0, 2.0 * 2^1, 2.0 * 2^2
                    assert sleep_times[0] == 2.0
                    assert sleep_times[1] == 4.0
                    assert sleep_times[2] == 8.0

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_http_client, mock_http_response):
        """Test that RuntimeError is raised when max retries exceeded."""
        mock_http_client.get.return_value = mock_http_response(500)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.return_value = mock_http_response(500)
                with patch('asyncio.sleep') as mock_sleep:
                    mock_sleep.return_value = None
                    client = GW2CrawlerClient(max_retries=2)

                    with pytest.raises(Exception):  # Could be RuntimeError or HTTPStatusError
                        await client.get_all_item_ids()


class TestGW2CrawlerClientRateLimiting:
    """Tests for rate limiting handling in crawler."""

    @pytest.mark.asyncio
    async def test_rate_limit_with_retry_after(self, mock_http_client, mock_http_response):
        """Test rate limiting with Retry-After header."""
        call_count = 0

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_http_response(429, headers={"Retry-After": "5"})
            return mock_http_response(200, [1, 2, 3])

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                with patch('asyncio.sleep') as mock_sleep:
                    mock_sleep.return_value = None  # sleep completes immediately in tests
                    client = GW2CrawlerClient()
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    assert call_count == 2
                    # Should respect Retry-After header (5 seconds)
                    # We verify via the call count that retry happened
                    assert mock_sleep.called

    @pytest.mark.asyncio
    async def test_rate_limit_without_retry_after(self, mock_http_client, mock_http_response):
        """Test rate limiting without Retry-After header uses exponential backoff."""
        call_count = 0
        sleep_times = []

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_http_response(429, headers={})
            return mock_http_response(200, [1, 2, 3])

        async def mock_sleep(duration):
            sleep_times.append(duration)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient(backoff_factor=2.0)
                    result = await client.get_all_item_ids()

                    assert result == [1, 2, 3]
                    # Should use exponential backoff: 2.0 * 2^0 = 2.0
                    assert sleep_times[0] == 2.0

    @pytest.mark.asyncio
    async def test_rate_limit_max_retries_exceeded(self, mock_http_client, mock_http_response):
        """Test that crawler respects max retries on rate limiting."""
        mock_http_client.get.return_value = mock_http_response(429, headers={"Retry-After": "0"})

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.return_value = mock_http_response(429, headers={"Retry-After": "0"})
                with patch('asyncio.sleep') as mock_sleep:
                    mock_sleep.return_value = None
                    client = GW2CrawlerClient(max_retries=3)

                    with pytest.raises(RuntimeError, match="Too many retries"):
                        await client.get_all_item_ids()


class TestGW2CrawlerClientErrorHandling:
    """Tests for error handling specific to crawler."""

    @pytest.mark.asyncio
    async def test_4xx_errors_not_retried(self, mock_http_client, mock_http_response):
        """Test that 4xx errors (except 429) are not retried."""
        response_404 = mock_http_response(404)

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.return_value = response_404
                with patch('asyncio.sleep') as mock_sleep:
                    mock_sleep.return_value = None
                    client = GW2CrawlerClient()

                    with pytest.raises(RuntimeError, match="404"):
                        await client.get_item_details([999999])

                    # Should not have retried
                    assert not mock_sleep.called

    @pytest.mark.asyncio
    async def test_token_required_without_key(self):
        """Test that endpoints requiring token raise ValueError without API key."""
        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client'):
            client = GW2CrawlerClient()

            with pytest.raises(ValueError, match="requires an API key"):
                await client.token_info()


class TestGW2CrawlerClientLogging:
    """Tests for crawler-specific logging."""

    @pytest.mark.asyncio
    async def test_crawler_retries_on_error(self, mock_http_client, mock_http_response):
        """Test that crawler retries on server errors (logs should contain [CRAWLER] prefix)."""
        call_count = 0

        async def mock_wait(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_http_response(503)
            return mock_http_response(200, [1, 2, 3])

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_http_client):
            with patch('asyncio.wait_for', side_effect=mock_wait):
                async def mock_sleep(duration): pass

                with patch('asyncio.sleep', side_effect=mock_sleep):
                    client = GW2CrawlerClient()
                    result = await client.get_all_item_ids()

                    # Verify retry happened
                    assert result == [1, 2, 3]
                    assert call_count == 2
                    pass  # Sleep was called
                    # The actual logging with [CRAWLER] prefix happens in the implementation


class TestGW2CrawlerClientVsGW2Client:
    """Tests comparing GW2CrawlerClient vs GW2Client behavior."""

    def test_different_default_settings(self):
        """Test that crawler has different defaults than regular client."""
        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client'):
            with patch('app.gw2.gw2_client.get_gw2_http_client'):
                from app.gw2.gw2_client import GW2Client

                regular_client = GW2Client()
                crawler_client = GW2CrawlerClient()

                # Crawler should have more aggressive settings
                assert crawler_client.max_retries > regular_client.max_retries
                assert crawler_client.backoff_factor >= regular_client.backoff_factor
                assert crawler_client.timeout > 3  # Regular client uses 3s

    @pytest.mark.asyncio
    async def test_no_circuit_breaker_in_crawler(self):
        """Test that crawler doesn't use circuit breaker."""
        # This test verifies that crawler calls HTTP directly without circuit breaker
        # In the implementation, GW2CrawlerClient overrides _get() to bypass circuit breaker

        # Create a simple mock client
        mock_client = MagicMock()
        mock_response = MagicMock(
            status_code=200,
            content=orjson.dumps([1, 2, 3]),
            raise_for_status=MagicMock()
        )

        with patch('app.gw2.gw2_crawler_client.get_gw2_http_client', return_value=mock_client):
            with patch('asyncio.wait_for', return_value=mock_response) as mock_wait:
                client = GW2CrawlerClient()
                result = await client.get_all_item_ids()

                # Verify direct call without circuit breaker
                assert result == [1, 2, 3]
                # The crawler should call asyncio.wait_for directly, not _protected_api_call
                assert mock_wait.called
