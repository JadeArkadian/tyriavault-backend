"""
Integration tests for /worlds endpoint.

This test verifies that:
1. The application responds to /worlds endpoint
2. The endpoint returns a list of worlds
3. Each world has the correct structure with all language translations
4. The data is fetched correctly from database or GW2 API (WireMock mock)

Note: These tests use WireMock to mock the GW2 API responses.
Test data is defined in: app/tests/integration/wiremock/mappings/gw2-api-mappings.json
"""
import httpx
import pytest


class WorldsEndpointClient:
    """Client to interact with the worlds endpoint during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_worlds(self) -> httpx.Response:
        """Get all worlds from the API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/worlds")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_returns_success():
    """
    Test that the /worlds endpoint responds with 200 status code.
    """
    client = WorldsEndpointClient()

    response = await client.get_worlds()

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /worlds endpoint responded successfully with status {response.status_code}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_returns_list():
    """
    Test that the /worlds endpoint returns a list of worlds.
    """
    client = WorldsEndpointClient()

    response = await client.get_worlds()
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Response should contain at least one world"

    print(f"✅ /worlds endpoint returned {len(data)} worlds")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_data_structure():
    """
    Test that each world in the response has the correct structure:
    - id: integer
    - name: dict with keys 'es', 'en', 'fr', 'de'
    """
    client = WorldsEndpointClient()

    response = await client.get_worlds()
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Response should contain at least one world"

    # Check first world structure
    first_world = data[0]

    # Verify 'id' field
    assert "id" in first_world, "World should have 'id' field"
    assert isinstance(first_world["id"], int), "'id' should be an integer"

    # Verify 'name' field
    assert "name" in first_world, "World should have 'name' field"
    assert isinstance(first_world["name"], dict), "'name' should be a dictionary"

    # Verify all language keys exist
    required_langs = ["es", "en", "fr", "de"]
    name_dict = first_world["name"]

    for lang in required_langs:
        assert lang in name_dict, f"'name' should have '{lang}' key"
        assert isinstance(name_dict[lang], str), f"'name[{lang}]' should be a string"
        assert len(name_dict[lang]) > 0, f"'name[{lang}]' should not be empty"

    print(f"✅ World structure is correct")
    print(f"   Example world: id={first_world['id']}, name_en={name_dict['en']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_all_worlds_have_valid_structure():
    """
    Test that ALL worlds in the response have valid structure.
    """
    client = WorldsEndpointClient()

    response = await client.get_worlds()
    assert response.status_code == 200

    data = response.json()
    required_langs = ["es", "en", "fr", "de"]

    for idx, world in enumerate(data):
        # Verify basic structure
        assert "id" in world, f"World at index {idx} missing 'id' field"
        assert "name" in world, f"World at index {idx} missing 'name' field"

        # Verify id is valid
        assert isinstance(world["id"], int), f"World at index {idx}: 'id' should be integer"
        assert world["id"] > 0, f"World at index {idx}: 'id' should be positive"

        # Verify name structure
        assert isinstance(world["name"], dict), f"World at index {idx}: 'name' should be dict"

        # Verify all languages are present
        for lang in required_langs:
            assert lang in world["name"], \
                f"World {world['id']} missing language '{lang}'"
            assert isinstance(world["name"][lang], str), \
                f"World {world['id']}: name[{lang}] should be string"
            assert len(world["name"][lang]) > 0, \
                f"World {world['id']}: name[{lang}] should not be empty"

    print(f"✅ All {len(data)} worlds have valid structure")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_has_known_worlds():
    """
    Test that the response contains expected test worlds from WireMock.
    This validates that we're getting data correctly.
    """
    client = WorldsEndpointClient()

    response = await client.get_worlds()
    assert response.status_code == 200

    data = response.json()
    world_ids = [world["id"] for world in data]

    # Test world IDs from WireMock mock data
    # These are the worlds configured in wiremock/mappings/gw2-api-mappings.json
    expected_test_world_ids = [1001, 1002, 2001]  # Anvil Rock, Borlis Pass, Gandara (test data)

    found_test_worlds = [wid for wid in expected_test_world_ids if wid in world_ids]

    assert len(found_test_worlds) > 0, \
        f"Should contain at least one expected test world ID. Found world IDs: {world_ids}"

    print(f"✅ Found {len(found_test_worlds)} test worlds out of {len(expected_test_world_ids)} expected")
    print(f"   Total worlds in response: {len(data)}")

    # Show some example worlds
    example_worlds = data[:3]
    print(f"   Example worlds:")
    for world in example_worlds:
        print(f"     - {world['id']}: {world['name']['en']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worlds_endpoint_response_time():
    """
    Test that the /worlds endpoint responds within acceptable time.
    Should be fast due to caching.
    """
    client = WorldsEndpointClient()

    import time

    # First request (might hit database or API)
    start_time = time.time()
    response1 = await client.get_worlds()
    first_request_time = time.time() - start_time

    assert response1.status_code == 200

    # Second request (should hit cache)
    start_time = time.time()
    response2 = await client.get_worlds()
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
