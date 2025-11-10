"""
Integration tests for /account and /account/wallet endpoints.

This test verifies that:
1. The application responds to /account endpoint with valid API key
2. The endpoint returns the correct account information structure
3. The /account/wallet endpoint returns wallet data correctly
4. API key authentication is required and validated
5. Invalid/missing API keys are properly rejected
6. The data is fetched and cached correctly

Note: These tests use WireMock to mock the GW2 API responses.
Test data is defined in: app/tests/integration/wiremock/mappings/gw2-api-mappings.json
"""
from datetime import datetime
from uuid import UUID

import httpx
import pytest


class AccountEndpointClient:
    """Client to interact with the account endpoints during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_account(self, api_key: str) -> httpx.Response:
        """Get account info from the API with authentication."""
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                f"{self.base_url}/api/v1/account",
                headers=headers
            )

    async def get_account_without_auth(self) -> httpx.Response:
        """Get account info without authentication header."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/account")

    async def get_wallet(self, api_key: str) -> httpx.Response:
        """Get wallet info from the API with authentication."""
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                f"{self.base_url}/api/v1/account/wallet",
                headers=headers
            )

    async def get_wallet_without_auth(self) -> httpx.Response:
        """Get wallet info without authentication header."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/account/wallet")


# ========================================
# ACCOUNT ENDPOINT TESTS
# ========================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_requires_authentication():
    """
    Test that the /account endpoint requires authentication.
    Should return 422 (Unprocessable Entity) when Authorization header is missing.
    """
    client = AccountEndpointClient()

    response = await client.get_account_without_auth()

    # FastAPI returns 422 for missing required headers
    assert response.status_code == 422, \
        f"Expected status code 422 for missing auth, got {response.status_code}"

    print(f"✅ /account endpoint correctly requires authentication (status {response.status_code})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_with_valid_api_key():
    """
    Test that the /account endpoint responds successfully with a valid API key.
    """
    client = AccountEndpointClient()

    # Use a test API key in GW2 format (similar to real API keys)
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    response = await client.get_account(test_api_key)

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /account endpoint responded successfully with valid API key")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_returns_correct_structure():
    """
    Test that the /account endpoint returns the correct data structure:
    - uuid: UUID
    - account_name: string
    - creation_date: datetime
    - fractal_level: int
    - world_name: dict with language codes
    - content_access: list of strings
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_account(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Verify required fields exist
    required_fields = ["uuid", "account_name", "creation_date", "fractal_level",
                       "world_name", "content_access"]
    for field in required_fields:
        assert field in data, f"Response should have '{field}' field"

    # Verify uuid is a valid UUID
    try:
        UUID(data["uuid"])
    except ValueError:
        pytest.fail(f"'uuid' should be a valid UUID, got: {data['uuid']}")

    # Verify account_name is a string
    assert isinstance(data["account_name"], str), "'account_name' should be a string"
    assert len(data["account_name"]) > 0, "'account_name' should not be empty"

    # Verify creation_date is a valid datetime string
    try:
        datetime.fromisoformat(data["creation_date"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"'creation_date' should be a valid ISO datetime, got: {data['creation_date']}")

    # Verify fractal_level is an integer
    assert isinstance(data["fractal_level"], int), "'fractal_level' should be an integer"
    assert data["fractal_level"] >= 0, "'fractal_level' should be non-negative"

    # Verify world_name is a dict with language codes
    assert isinstance(data["world_name"], dict), "'world_name' should be a dict"
    expected_languages = ["es", "en", "fr", "de"]
    for lang in expected_languages:
        assert lang in data["world_name"], f"'world_name' should have '{lang}' key"

    # Verify content_access is a list
    assert isinstance(data["content_access"], list), "'content_access' should be a list"

    print(f"✅ Account structure is correct")
    print(f"   UUID: {data['uuid']}")
    print(f"   Account Name: {data['account_name']}")
    print(f"   Fractal Level: {data['fractal_level']}")
    print(f"   Content Access: {data['content_access']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_has_expected_data():
    """
    Test that the response contains expected account data from WireMock.
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_account(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Expected values from WireMock configuration
    assert data["account_name"] == "TestAccount.1234", \
        f"Expected account_name 'TestAccount.1234', got '{data['account_name']}'"

    assert data["fractal_level"] == 100, \
        f"Expected fractal_level 100, got {data['fractal_level']}"

    # Verify UUID matches the one from WireMock
    expected_uuid = "12345678-90AB-CDEF-1234-567890ABCDEF"
    assert data["uuid"].upper() == expected_uuid.upper(), \
        f"Expected UUID '{expected_uuid}', got '{data['uuid']}'"

    print(f"✅ Account data matches expected values from WireMock")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_with_invalid_bearer_format():
    """
    Test that the endpoint properly rejects invalid Bearer token format.
    """
    client = AccountEndpointClient()

    # Test with invalid format (no "Bearer " prefix)
    headers = {"Authorization": "INVALID-FORMAT-KEY"}
    async with httpx.AsyncClient(timeout=client.timeout) as http_client:
        response = await http_client.get(
            f"{client.base_url}/api/v1/account",
            headers=headers
        )

    # Should return 400 for invalid Bearer format
    assert response.status_code == 400, \
        f"Expected status code 400 for invalid Bearer format, got {response.status_code}"

    print(f"✅ /account endpoint correctly rejects invalid Bearer format")


# ========================================
# WALLET ENDPOINT TESTS
# ========================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_requires_authentication():
    """
    Test that the /account/wallet endpoint requires authentication.
    Should return 422 (Unprocessable Entity) when Authorization header is missing.
    """
    client = AccountEndpointClient()

    response = await client.get_wallet_without_auth()

    # FastAPI returns 422 for missing required headers
    assert response.status_code == 422, \
        f"Expected status code 422 for missing auth, got {response.status_code}"

    print(f"✅ /account/wallet endpoint correctly requires authentication (status {response.status_code})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_with_valid_api_key():
    """
    Test that the /account/wallet endpoint responds successfully with a valid API key.
    """
    client = AccountEndpointClient()

    # Use a test API key in GW2 format (similar to real API keys)
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    response = await client.get_wallet(test_api_key)

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /account/wallet endpoint responded successfully with valid API key")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_returns_correct_structure():
    """
    Test that the /account/wallet endpoint returns the correct data structure:
    - Returns a list of wallet items
    - Each item has: currency_id, amount, currency_name, currency_icon, currency_description
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_wallet(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Verify it's a list
    assert isinstance(data, list), "Response should be a list"

    # Verify list is not empty
    assert len(data) > 0, "Wallet should contain at least one currency"

    # Verify structure of first item
    first_item = data[0]
    required_fields = ["currency_id", "amount", "currency_name",
                       "currency_icon", "currency_description"]

    for field in required_fields:
        assert field in first_item, f"Wallet item should have '{field}' field"

    # Verify currency_id is an integer
    assert isinstance(first_item["currency_id"], int), "'currency_id' should be an integer"
    assert first_item["currency_id"] > 0, "'currency_id' should be positive"

    # Verify amount is an integer
    assert isinstance(first_item["amount"], int), "'amount' should be an integer"
    assert first_item["amount"] >= 0, "'amount' should be non-negative"

    # Verify currency_name is a dict with language codes
    assert isinstance(first_item["currency_name"], dict), "'currency_name' should be a dict"
    expected_languages = ["es", "en", "fr", "de"]
    for lang in expected_languages:
        assert lang in first_item["currency_name"], \
            f"'currency_name' should have '{lang}' key"

    # Verify currency_description is a dict with language codes
    assert isinstance(first_item["currency_description"], dict), \
        "'currency_description' should be a dict"
    for lang in expected_languages:
        assert lang in first_item["currency_description"], \
            f"'currency_description' should have '{lang}' key"

    print(f"✅ Wallet structure is correct")
    print(f"   Number of currencies: {len(data)}")
    print(f"   First currency ID: {first_item['currency_id']}")
    print(f"   First currency amount: {first_item['amount']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_has_expected_currencies():
    """
    Test that the response contains expected currency data from WireMock.
    WireMock returns currencies with IDs 1, 2, and 4.
    Note: Only currencies that exist in the database will be returned.
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_wallet(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Verify we have at least some currencies
    assert len(data) > 0, "Wallet should contain at least one currency"

    # Get currency IDs from response
    currency_ids = [item["currency_id"] for item in data]

    # Verify Coin (ID 1) - should always be present
    coin_item = next((item for item in data if item["currency_id"] == 1), None)
    assert coin_item is not None, "Coin (ID 1) should be in wallet"
    assert coin_item["amount"] == 123456789, \
        f"Expected Coin amount 123456789, got {coin_item['amount']}"

    # Verify Karma (ID 2) - should always be present
    karma_item = next((item for item in data if item["currency_id"] == 2), None)
    assert karma_item is not None, "Karma (ID 2) should be in wallet"
    assert karma_item["amount"] == 50000, \
        f"Expected Karma amount 50000, got {karma_item['amount']}"

    # Verify Gems (ID 4) - if present in database
    gems_item = next((item for item in data if item["currency_id"] == 4), None)
    if gems_item is not None:
        assert gems_item["amount"] == 1000, \
            f"Expected Gems amount 1000, got {gems_item['amount']}"
        print(f"✅ Wallet contains expected currencies from WireMock (including Gems)")
    else:
        print(f"✅ Wallet contains expected currencies from WireMock (Gems not in database)")

    print(f"   Found currency IDs: {currency_ids}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_with_invalid_bearer_format():
    """
    Test that the endpoint properly rejects invalid Bearer token format.
    """
    client = AccountEndpointClient()

    # Test with invalid format (no "Bearer " prefix)
    headers = {"Authorization": "INVALID-FORMAT-KEY"}
    async with httpx.AsyncClient(timeout=client.timeout) as http_client:
        response = await http_client.get(
            f"{client.base_url}/api/v1/account/wallet",
            headers=headers
        )

    # Should return 400 for invalid Bearer format
    assert response.status_code == 400, \
        f"Expected status code 400 for invalid Bearer format, got {response.status_code}"

    print(f"✅ /account/wallet endpoint correctly rejects invalid Bearer format")


# ========================================
# CACHING TESTS
# ========================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_endpoint_caching():
    """
    Test that the /account endpoint properly caches responses.
    Multiple requests with same API key should return consistent data.
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-CACHE-TEST"

    # Make first request
    response1 = await client.get_account(test_api_key)
    assert response1.status_code == 200
    data1 = response1.json()

    # Make second request immediately
    response2 = await client.get_account(test_api_key)
    assert response2.status_code == 200
    data2 = response2.json()

    # Data should be identical (cached)
    assert data1 == data2, "Cached responses should be identical"

    print(f"✅ /account endpoint caching works correctly")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_endpoint_caching():
    """
    Test that the /account/wallet endpoint properly caches responses.
    Multiple requests with same API key should return consistent data.
    """
    client = AccountEndpointClient()
    test_api_key = "TEST-API-KEY-CACHE-TEST"

    # Make first request
    response1 = await client.get_wallet(test_api_key)
    assert response1.status_code == 200
    data1 = response1.json()

    # Make second request immediately
    response2 = await client.get_wallet(test_api_key)
    assert response2.status_code == 200
    data2 = response2.json()

    # Data should be identical (cached)
    assert data1 == data2, "Cached responses should be identical"

    print(f"✅ /account/wallet endpoint caching works correctly")
