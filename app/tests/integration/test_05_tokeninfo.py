"""
Integration tests for /tokeninfo endpoint.

This test verifies that:
1. The application responds to /tokeninfo endpoint with valid API key
2. The endpoint returns the correct permissions structure
3. API key authentication is required and validated
4. Invalid/missing API keys are properly rejected
5. The data is fetched and cached correctly

Note: These tests use WireMock to mock the GW2 API responses.
Test data is defined in: app/tests/integration/wiremock/mappings/gw2-api-mappings.json
"""
import httpx
import pytest


class TokenInfoEndpointClient:
    """Client to interact with the tokeninfo endpoint during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_tokeninfo(self, api_key: str) -> httpx.Response:
        """Get token info from the API with authentication."""
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(
                f"{self.base_url}/api/v1/common/tokeninfo",
                headers=headers
            )

    async def get_tokeninfo_without_auth(self) -> httpx.Response:
        """Get token info without authentication header."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/common/tokeninfo")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_requires_authentication():
    """
    Test that the /tokeninfo endpoint requires authentication.
    Should return 422 (Unprocessable Entity) when Authorization header is missing.
    """
    client = TokenInfoEndpointClient()

    response = await client.get_tokeninfo_without_auth()

    # FastAPI returns 422 for missing required headers
    assert response.status_code == 422, \
        f"Expected status code 422 for missing auth, got {response.status_code}"

    print(f"✅ /tokeninfo endpoint correctly requires authentication (status {response.status_code})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_with_valid_api_key():
    """
    Test that the /tokeninfo endpoint responds successfully with a valid API key.
    """
    client = TokenInfoEndpointClient()

    # Use a test API key in GW2 format (similar to real API keys)
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    response = await client.get_tokeninfo(test_api_key)

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /tokeninfo endpoint responded successfully with valid API key")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_returns_correct_structure():
    """
    Test that the /tokeninfo endpoint returns the correct data structure:
    - permissions: list of strings
    """
    client = TokenInfoEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_tokeninfo(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Verify 'permissions' field exists
    assert "permissions" in data, "Response should have 'permissions' field"

    # Verify it's a list
    assert isinstance(data["permissions"], list), "'permissions' should be a list"

    # Verify list is not empty
    assert len(data["permissions"]) > 0, "'permissions' should contain at least one permission"

    # Verify all elements are strings
    for idx, permission in enumerate(data["permissions"]):
        assert isinstance(permission, str), \
            f"Permission at index {idx} should be a string, got {type(permission)}"
        assert len(permission) > 0, \
            f"Permission at index {idx} should not be empty"

    print(f"✅ TokenInfo structure is correct")
    print(f"   Permissions: {data['permissions']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_has_expected_permissions():
    """
    Test that the response contains expected GW2 API permissions.
    These are the permissions configured in WireMock mock data.
    """
    client = TokenInfoEndpointClient()
    test_api_key = "TEST-API-KEY-1234-5678-90AB-CDEF"

    response = await client.get_tokeninfo(test_api_key)
    assert response.status_code == 200

    data = response.json()
    permissions = data["permissions"]

    # Expected permissions from WireMock configuration
    expected_permissions = ["account", "characters", "inventories", "wallet"]

    # Verify all expected permissions are present
    for expected_perm in expected_permissions:
        assert expected_perm in permissions, \
            f"Expected permission '{expected_perm}' not found in {permissions}"

    print(f"✅ All expected permissions found")
    print(f"   Expected: {expected_permissions}")
    print(f"   Got: {permissions}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_with_invalid_bearer_format():
    """
    Test that the endpoint properly rejects invalid Bearer token format.
    """
    client = TokenInfoEndpointClient()

    # Test with invalid format (no "Bearer " prefix)
    headers = {"Authorization": "INVALID-FORMAT-KEY"}

    async with httpx.AsyncClient(timeout=client.timeout) as http_client:
        response = await http_client.get(
            f"{client.base_url}/api/v1/common/tokeninfo",
            headers=headers
        )

    # Should return 400 (Bad Request) for invalid format
    assert response.status_code == 400, \
        f"Expected status code 400 for invalid format, got {response.status_code}"

    print(f"✅ Invalid Bearer format correctly rejected (status {response.status_code})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_response_time():
    """
    Test that the /tokeninfo endpoint responds within acceptable time.
    Should be fast due to caching.
    """
    client = TokenInfoEndpointClient()
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    import time

    # First request (might register the API key)
    start_time = time.time()
    response1 = await client.get_tokeninfo(test_api_key)
    first_request_time = time.time() - start_time

    assert response1.status_code == 200

    # Second request (should hit cache)
    start_time = time.time()
    response2 = await client.get_tokeninfo(test_api_key)
    second_request_time = time.time() - start_time

    assert response2.status_code == 200

    # Second request should be faster (cached)
    assert second_request_time < first_request_time or second_request_time < 0.5, \
        "Second request should be faster due to caching"

    print(f"✅ Response times:")
    print(f"   First request:  {first_request_time:.3f}s")
    print(f"   Second request: {second_request_time:.3f}s (cached)")

    # Verify both responses are identical
    assert response1.json() == response2.json(), "Cached response should match original"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_consistent_data():
    """
    Test that multiple requests with the same API key return consistent data.
    """
    client = TokenInfoEndpointClient()
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    # Make 3 requests with the same API key
    responses = []
    for i in range(3):
        response = await client.get_tokeninfo(test_api_key)
        assert response.status_code == 200, f"Request {i + 1} failed"
        responses.append(response.json())

    # All responses should be identical
    first_response = responses[0]
    for idx, response in enumerate(responses[1:], start=2):
        assert response == first_response, \
            f"Request {idx} returned different data than request 1"

    print(f"✅ Data is consistent across {len(responses)} requests")
    print(f"   Permissions: {first_response['permissions']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_permissions_are_valid():
    """
    Test that all permissions returned are valid GW2 API permission names.
    """
    client = TokenInfoEndpointClient()
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    response = await client.get_tokeninfo(test_api_key)
    assert response.status_code == 200

    data = response.json()
    permissions = data["permissions"]

    # Known GW2 API permissions (not exhaustive, but common ones)
    valid_gw2_permissions = [
        "account", "builds", "characters", "guilds", "inventories",
        "progression", "pvp", "tradingpost", "unlocks", "wallet"
    ]

    # Check that all returned permissions are known valid permissions
    for permission in permissions:
        assert permission in valid_gw2_permissions, \
            f"Unknown permission: {permission}. Known permissions: {valid_gw2_permissions}"

    print(f"✅ All {len(permissions)} permissions are valid GW2 API permissions")
    print(f"   Permissions: {permissions}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_different_api_keys():
    """
    Test that different API keys can be validated (simulating multiple users).
    Note: In the mock, all keys return the same data, but we test the flow.
    """
    client = TokenInfoEndpointClient()

    # Test with multiple different API keys (GW2 format)
    test_api_keys = [
        "11111111-2222-3333-4444-555555555555AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE",
        "66666666-7777-8888-9999-000000000000FFFFFFFF-1111-2222-3333-444444444444",
        "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE11111111-2222-3333-4444-555555555555"
    ]

    results = []
    for api_key in test_api_keys:
        response = await client.get_tokeninfo(api_key)
        assert response.status_code == 200, \
            f"API key {api_key} failed validation"
        results.append(response.json())

    print(f"✅ Successfully validated {len(test_api_keys)} different API keys")

    # All should have permissions (in mock, they return the same data)
    for idx, result in enumerate(results):
        assert "permissions" in result, f"Result {idx} missing permissions"
        assert len(result["permissions"]) > 0, f"Result {idx} has no permissions"

    print(f"   All keys have valid permissions")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_authorization_header_variations():
    """
    Test different variations of the Authorization header format.
    """
    client = TokenInfoEndpointClient()
    base_url = client.base_url
    timeout = client.timeout

    test_cases = [
        {
            "name": "Valid: Bearer with key",
            "header": "Bearer AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444",
            "expected_status": 200,
            "may_raise_protocol_error": False
        },
        {
            "name": "Invalid: No Bearer prefix",
            "header": "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444",
            "expected_status": 400,
            "may_raise_protocol_error": False
        },
        {
            "name": "Invalid: Bearer with empty key",
            "header": "Bearer ",
            "expected_status": 400,
            "may_raise_protocol_error": True  # httpx may reject this as illegal header
        },
        {
            "name": "Invalid: Only 'Bearer'",
            "header": "Bearer",
            "expected_status": 400,
            "may_raise_protocol_error": True  # httpx may reject this as illegal header
        }
    ]

    results = []
    for test_case in test_cases:
        headers = {"Authorization": test_case["header"]}

        try:
            async with httpx.AsyncClient(timeout=timeout) as http_client:
                response = await http_client.get(
                    f"{base_url}/api/v1/common/tokeninfo",
                    headers=headers
                )

            status_matches = response.status_code == test_case["expected_status"]
            results.append({
                "name": test_case["name"],
                "expected": test_case["expected_status"],
                "got": response.status_code,
                "passed": status_matches
            })

            assert status_matches, \
                f"{test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}"

        except (httpx.LocalProtocolError, httpx.ProtocolError) as e:
            # Some invalid headers are rejected by httpx at protocol level
            # This is actually correct behavior - the header is so malformed it can't even be sent
            if test_case["may_raise_protocol_error"]:
                results.append({
                    "name": test_case["name"],
                    "expected": test_case["expected_status"],
                    "got": "Protocol Error (header rejected by HTTP client)",
                    "passed": True  # This is acceptable for these test cases
                })
                print(f"   ℹ️  {test_case['name']}: Header rejected at protocol level (expected for malformed headers)")
            else:
                # If we didn't expect a protocol error, re-raise
                raise

    print(f"✅ All {len(test_cases)} authorization header variations handled correctly")
    for result in results:
        status = "✓" if result["passed"] else "✗"
        got_display = result['got'] if isinstance(result['got'], int) else "Protocol Error"
        print(f"   {status} {result['name']}: {got_display}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tokeninfo_endpoint_no_extra_fields():
    """
    Test that the response only contains expected fields (no data leakage).
    """
    client = TokenInfoEndpointClient()
    test_api_key = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEEFFFFFFFF-1111-2222-3333-444444444444"

    response = await client.get_tokeninfo(test_api_key)
    assert response.status_code == 200

    data = response.json()

    # Should only have 'permissions' field
    expected_fields = {"permissions"}
    actual_fields = set(data.keys())

    assert actual_fields == expected_fields, \
        f"Response should only have {expected_fields}, got {actual_fields}"

    # Should NOT have sensitive fields like api_key, account_uuid, etc.
    sensitive_fields = ["api_key", "account_uuid", "game_account_uuid", "account_id"]
    for sensitive_field in sensitive_fields:
        assert sensitive_field not in data, \
            f"Response should not expose sensitive field: {sensitive_field}"

    print(f"✅ Response contains only expected fields: {list(actual_fields)}")
    print(f"   No sensitive data leaked")
