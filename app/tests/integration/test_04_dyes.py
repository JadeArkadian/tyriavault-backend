"""
Integration tests for /dyes endpoint.

This test verifies that:
1. The application responds to /dyes endpoint
2. The endpoint returns a list of dyes
3. Each dye has the correct structure with all language translations
4. Each dye has a valid hexcolor format
5. The data is fetched correctly from GW2 API (WireMock mock) or database

Note: These tests use WireMock to mock the GW2 API responses.
Test data is defined in: app/tests/integration/wiremock/mappings/gw2-api-mappings.json
"""
import re

import httpx
import pytest


class DyesEndpointClient:
    """Client to interact with the dyes endpoint during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_dyes(self) -> httpx.Response:
        """Get all dyes from the API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/dyes")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_returns_success():
    """
    Test that the /dyes endpoint responds with 200 status code.
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /dyes endpoint responded successfully with status {response.status_code}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_returns_list():
    """
    Test that the /dyes endpoint returns a list of dyes.
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Response should contain at least one dye"

    print(f"✅ /dyes endpoint returned {len(data)} dyes")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_data_structure():
    """
    Test that each dye in the response has the correct structure:
    - id: integer
    - name: dict with keys 'es', 'en', 'fr', 'de'
    - hexcolor: string in hex format (#RRGGBB)
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Response should contain at least one dye"

    # Check first dye structure
    first_dye = data[0]

    # Verify 'id' field
    assert "id" in first_dye, "Dye should have 'id' field"
    assert isinstance(first_dye["id"], int), "'id' should be an integer"

    # Verify 'name' field
    assert "name" in first_dye, "Dye should have 'name' field"
    assert isinstance(first_dye["name"], dict), "'name' should be a dictionary"

    # Verify all language keys exist
    required_langs = ["es", "en", "fr", "de"]
    name_dict = first_dye["name"]

    for lang in required_langs:
        assert lang in name_dict, f"'name' should have '{lang}' key"
        assert isinstance(name_dict[lang], str), f"'name[{lang}]' should be a string"
        assert len(name_dict[lang]) > 0, f"'name[{lang}]' should not be empty"

    # Verify 'hexcolor' field
    assert "hexcolor" in first_dye, "Dye should have 'hexcolor' field"
    assert isinstance(first_dye["hexcolor"], str), "'hexcolor' should be a string"

    # Verify hexcolor format (#RRGGBB)
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
    assert hex_pattern.match(first_dye["hexcolor"]), \
        f"'hexcolor' should be in hex format #RRGGBB, got: {first_dye['hexcolor']}"

    print(f"✅ Dye structure is correct")
    print(f"   Example dye: id={first_dye['id']}, name_en={name_dict['en']}, color={first_dye['hexcolor']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_all_dyes_have_valid_structure():
    """
    Test that ALL dyes in the response have valid structure.
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()
    assert response.status_code == 200

    data = response.json()
    required_langs = ["es", "en", "fr", "de"]
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')

    for idx, dye in enumerate(data):
        # Verify basic structure
        assert "id" in dye, f"Dye at index {idx} missing 'id' field"
        assert "name" in dye, f"Dye at index {idx} missing 'name' field"
        assert "hexcolor" in dye, f"Dye at index {idx} missing 'hexcolor' field"

        # Verify id is valid
        assert isinstance(dye["id"], int), f"Dye at index {idx}: 'id' should be integer"
        assert dye["id"] > 0, f"Dye at index {idx}: 'id' should be positive"

        # Verify name structure
        assert isinstance(dye["name"], dict), f"Dye at index {idx}: 'name' should be dict"

        # Verify all languages are present
        for lang in required_langs:
            assert lang in dye["name"], \
                f"Dye {dye['id']} missing language '{lang}'"
            assert isinstance(dye["name"][lang], str), \
                f"Dye {dye['id']}: name[{lang}] should be string"
            assert len(dye["name"][lang]) > 0, \
                f"Dye {dye['id']}: name[{lang}] should not be empty"

        # Verify hexcolor format
        assert isinstance(dye["hexcolor"], str), \
            f"Dye {dye['id']}: 'hexcolor' should be string"
        assert hex_pattern.match(dye["hexcolor"]), \
            f"Dye {dye['id']}: 'hexcolor' should be in hex format #RRGGBB, got: {dye['hexcolor']}"

    print(f"✅ All {len(data)} dyes have valid structure")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_has_known_dyes():
    """
    Test that the response contains expected test dyes from WireMock.
    This validates that we're getting data correctly.
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()
    assert response.status_code == 200

    data = response.json()
    dye_ids = [dye["id"] for dye in data]

    # Test dye IDs from WireMock mock data
    # ID 1 is "Dye Remover" configured in wiremock/mappings/gw2-api-mappings.json
    expected_test_dye_ids = [1]  # Dye Remover (test data)

    found_test_dyes = [did for did in expected_test_dye_ids if did in dye_ids]

    assert len(found_test_dyes) > 0, \
        f"Should contain at least one expected test dye ID. Found dye IDs: {dye_ids}"

    print(f"✅ Found {len(found_test_dyes)} test dyes out of {len(expected_test_dye_ids)} expected")
    print(f"   Total dyes in response: {len(data)}")

    # Show some example dyes
    example_dyes = data[:3] if len(data) >= 3 else data
    print(f"   Example dyes:")
    for dye in example_dyes:
        print(f"     - {dye['id']}: {dye['name']['en']} ({dye['hexcolor']})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_hexcolor_values():
    """
    Test that hexcolor values are valid RGB hex codes.
    """
    client = DyesEndpointClient()

    response = await client.get_dyes()
    assert response.status_code == 200

    data = response.json()

    for dye in data:
        hexcolor = dye["hexcolor"]

        # Should start with #
        assert hexcolor.startswith("#"), \
            f"Dye {dye['id']}: hexcolor should start with #, got: {hexcolor}"

        # Should be 7 characters (#RRGGBB)
        assert len(hexcolor) == 7, \
            f"Dye {dye['id']}: hexcolor should be 7 characters, got: {hexcolor}"

        # Should be valid hex (can be converted to RGB)
        try:
            r = int(hexcolor[1:3], 16)
            g = int(hexcolor[3:5], 16)
            b = int(hexcolor[5:7], 16)

            # RGB values should be 0-255
            assert 0 <= r <= 255, f"Dye {dye['id']}: R value out of range"
            assert 0 <= g <= 255, f"Dye {dye['id']}: G value out of range"
            assert 0 <= b <= 255, f"Dye {dye['id']}: B value out of range"

        except ValueError:
            pytest.fail(f"Dye {dye['id']}: Invalid hex color format: {hexcolor}")

    print(f"✅ All {len(data)} dyes have valid hex color values")

    # Show color distribution
    if len(data) > 0:
        example_dye = data[0]
        hex_val = example_dye["hexcolor"]
        r = int(hex_val[1:3], 16)
        g = int(hex_val[3:5], 16)
        b = int(hex_val[5:7], 16)
        print(f"   Example: {example_dye['name']['en']} = {hex_val} = RGB({r}, {g}, {b})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dyes_endpoint_response_time():
    """
    Test that the /dyes endpoint responds within acceptable time.
    Should be fast due to caching.
    """
    client = DyesEndpointClient()

    import time

    # First request (might hit GW2 API or database)
    start_time = time.time()
    response1 = await client.get_dyes()
    first_request_time = time.time() - start_time

    assert response1.status_code == 200

    # Second request (should hit cache)
    start_time = time.time()
    response2 = await client.get_dyes()
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
async def test_dyes_endpoint_consistent_data():
    """
    Test that multiple requests return consistent data.
    This validates data integrity and cache consistency.
    """
    client = DyesEndpointClient()

    # Make 3 requests
    responses = []
    for i in range(3):
        response = await client.get_dyes()
        assert response.status_code == 200, f"Request {i + 1} failed"
        responses.append(response.json())

    # All responses should be identical
    first_response = responses[0]
    for idx, response in enumerate(responses[1:], start=2):
        assert response == first_response, \
            f"Request {idx} returned different data than request 1"

    # Check that IDs are unique (no duplicates)
    dye_ids = [dye["id"] for dye in first_response]
    unique_ids = set(dye_ids)

    assert len(dye_ids) == len(unique_ids), \
        f"Duplicate dye IDs found. Total: {len(dye_ids)}, Unique: {len(unique_ids)}"

    print(f"✅ Data is consistent across {len(responses)} requests")
    print(f"   Total dyes: {len(first_response)}")
    print(f"   All IDs unique: {len(unique_ids)} dyes")
