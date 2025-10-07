import httpx
import pytest

from app.gw2.client import GW2Client

# Base URL to verify
BASE_URL = "https://api.guildwars2.com/v2"

# --- Mock Response Class ---

class MockResponse:
    """
    Simulates a response object from the httpx library for testing purposes.
    """
    def __init__(self, status_code, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = str(json_data) # Used by raise_for_status if it fails

    def json(self):
        """Simulates response.json()"""
        return self._json_data

    def raise_for_status(self):
        """
        Simulates response.raise_for_status().
        Raises an exception for 4xx or 5xx status codes.
        """
        if 400 <= self.status_code < 600:
            raise httpx.HTTPStatusError(
                f"Client error for url: {BASE_URL}/endpoint",
                request=httpx.Request("GET", f"{BASE_URL}/endpoint"),
                response=self
            )

# -----------------------------

class TestGW2Client:

    # Fixtures run before each test

    @pytest.fixture
    def client_no_key(self):
        return GW2Client()

    @pytest.fixture
    def client_with_key(self):
        return GW2Client(api_key="TEST_API_KEY")

    ## Initialization and Configuration Tests

    def test_client_initialization_with_key_and_custom_timeout(self):
        """Verifies initialization with API key and custom timeout."""
        custom_client = GW2Client(timeout=5.5, api_key="CUSTOM_KEY")
        assert custom_client.api_key == "CUSTOM_KEY"
        assert custom_client.client.timeout.connect == 5.5

    def test_headers_no_key(self, client_no_key):
        """Verifies _headers() returns an empty dict if no API key is present."""
        assert client_no_key._headers() == {}

    def test_headers_with_key(self, client_with_key):
        """Verifies _headers() returns the Authorization header with the API key."""
        expected_headers = {"Authorization": "Bearer TEST_API_KEY"}
        assert client_with_key._headers() == expected_headers

    ## Private Method Tests (_get)

    def test_get_success(self, client_no_key, mocker):
        """Simulates a successful GET call and verifies the result."""
        mock_data = {"success": True, "value": 123}
        # Mock response.client.get to return a successful MockResponse
        mock_response = MockResponse(status_code=200, json_data=mock_data)
        # Use mocker to replace the actual httpx.Client.get method
        mocker.patch.object(client_no_key.client, 'get', return_value=mock_response)

        result = client_no_key._get("/test/endpoint", params={"q": "value"})

        # Assertions:
        # 1. The 'get' method was called exactly once.
        client_no_key.client.get.assert_called_once()
        # 2. It was called with the correct arguments (endpoint, params, headers).
        client_no_key.client.get.assert_called_with(
            "/test/endpoint",
            params={"q": "value"},
            headers={}
        )
        # 3. The result is the mocked JSON data.
        assert result == mock_data

    def test_get_failure_raises_exception(self, client_no_key, mocker):
        """Simulates a failed GET call (e.g., 404) and verifies the exception is raised."""
        # Simulate a 404 error
        mock_response = MockResponse(status_code=404, json_data={"text": "Page Not Found"})
        mocker.patch.object(client_no_key.client, 'get', return_value=mock_response)

        # Use pytest.raises to assert that the correct exception (HTTPStatusError) is thrown
        with pytest.raises(httpx.HTTPStatusError):
            client_no_key._get("/non/existent/endpoint")

    ## High-Level Method Tests

    def test_get_account(self, client_with_key, mocker):
        """Verifies get_account calls _get with the correct endpoint."""
        mock_data = {"id": "account-id", "name": "Test Account"}
        # Mock the private _get method to prevent actual API call
        mocker