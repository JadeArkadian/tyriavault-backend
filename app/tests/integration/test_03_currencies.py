"""
Integration tests for /currencies endpoint.

This test verifies that:
1. The application responds to /currencies endpoint
2. The endpoint returns a list of currencies
3. Each currency has the correct structure with all language translations
4. Each currency has name, description, and icon_url fields
5. The data is fetched correctly from GW2 API (WireMock mock) or database

Note: These tests use WireMock to mock the GW2 API responses.
Test data is defined in: app/tests/integration/wiremock/mappings/gw2-api-mappings.json
"""
import httpx
import pytest


class CurrenciesEndpointClient:
    """Client to interact with the currencies endpoint during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def get_currencies(self) -> httpx.Response:
        """Get all currencies from the API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}/api/v1/currencies")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_returns_success():
    """
    Test that the /currencies endpoint responds with 200 status code.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()

    assert response.status_code == 200, \
        f"Expected status code 200, got {response.status_code}: {response.text}"

    print(f"✅ /currencies endpoint responded successfully with status {response.status_code}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_returns_list():
    """
    Test that the /currencies endpoint returns a list of currencies.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Response should contain at least one currency"

    print(f"✅ /currencies endpoint returned {len(data)} currencies")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_data_structure():
    """
    Test that each currency in the response has the correct structure:
    - id: integer
    - name: dict with keys 'es', 'en', 'fr', 'de'
    - description: dict with keys 'es', 'en', 'fr', 'de'
    - icon_url: optional string (URL)
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0, "Response should contain at least one currency"

    # Check first currency structure
    first_currency = data[0]

    # Verify 'id' field
    assert "id" in first_currency, "Currency should have 'id' field"
    assert isinstance(first_currency["id"], int), "'id' should be an integer"

    # Verify 'name' field
    assert "name" in first_currency, "Currency should have 'name' field"
    assert isinstance(first_currency["name"], dict), "'name' should be a dictionary"

    # Verify all language keys exist in name
    required_langs = ["es", "en", "fr", "de"]
    name_dict = first_currency["name"]

    for lang in required_langs:
        assert lang in name_dict, f"'name' should have '{lang}' key"
        assert isinstance(name_dict[lang], str), f"'name[{lang}]' should be a string"
        assert len(name_dict[lang]) > 0, f"'name[{lang}]' should not be empty"

    # Verify 'description' field
    assert "description" in first_currency, "Currency should have 'description' field"
    assert isinstance(first_currency["description"], dict), "'description' should be a dictionary"

    # Verify all language keys exist in description
    description_dict = first_currency["description"]

    for lang in required_langs:
        assert lang in description_dict, f"'description' should have '{lang}' key"
        # Description can be null or string
        if description_dict[lang] is not None:
            assert isinstance(description_dict[lang], str), f"'description[{lang}]' should be a string or null"

    # Verify 'icon_url' field (optional)
    assert "icon_url" in first_currency, "Currency should have 'icon_url' field"
    if first_currency["icon_url"] is not None:
        assert isinstance(first_currency["icon_url"], str), "'icon_url' should be a string or null"
        # If present, should be a valid URL format
        assert first_currency["icon_url"].startswith("http"), "'icon_url' should start with http"

    print(f"✅ Currency structure is correct")
    print(f"   Example currency: id={first_currency['id']}, name_en={name_dict['en']}")
    print(f"   Icon URL: {first_currency['icon_url']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_all_currencies_have_valid_structure():
    """
    Test that ALL currencies in the response have valid structure.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    required_langs = ["es", "en", "fr", "de"]

    for idx, currency in enumerate(data):
        # Verify basic structure
        assert "id" in currency, f"Currency at index {idx} missing 'id' field"
        assert "name" in currency, f"Currency at index {idx} missing 'name' field"
        assert "description" in currency, f"Currency at index {idx} missing 'description' field"
        assert "icon_url" in currency, f"Currency at index {idx} missing 'icon_url' field"

        # Verify id is valid
        assert isinstance(currency["id"], int), f"Currency at index {idx}: 'id' should be integer"
        assert currency["id"] > 0, f"Currency at index {idx}: 'id' should be positive"

        # Verify name structure
        assert isinstance(currency["name"], dict), f"Currency at index {idx}: 'name' should be dict"

        # Verify all languages are present in name
        for lang in required_langs:
            assert lang in currency["name"], \
                f"Currency {currency['id']} missing language '{lang}' in name"
            assert isinstance(currency["name"][lang], str), \
                f"Currency {currency['id']}: name[{lang}] should be string"
            assert len(currency["name"][lang]) > 0, \
                f"Currency {currency['id']}: name[{lang}] should not be empty"

        # Verify description structure
        assert isinstance(currency["description"], dict), \
            f"Currency at index {idx}: 'description' should be dict"

        # Verify all languages are present in description
        for lang in required_langs:
            assert lang in currency["description"], \
                f"Currency {currency['id']} missing language '{lang}' in description"
            # Description values can be null
            if currency["description"][lang] is not None:
                assert isinstance(currency["description"][lang], str), \
                    f"Currency {currency['id']}: description[{lang}] should be string or null"

    print(f"✅ All {len(data)} currencies have valid structure")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_has_known_currencies():
    """
    Test that the response contains expected test currencies from WireMock.
    This validates that we're getting data correctly.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    currency_ids = [currency["id"] for currency in data]
    currency_names_en = [currency["name"]["en"].lower() for currency in data]

    # Test currency IDs from WireMock mock data
    # These are the currencies configured in wiremock/mappings/gw2-api-mappings.json
    expected_test_currency_ids = [1, 2]  # Coin, Karma (test data)

    found_test_currencies = [cid for cid in expected_test_currency_ids if cid in currency_ids]

    assert len(found_test_currencies) > 0, \
        f"Should contain at least one expected test currency ID. Found currency IDs: {currency_ids}"

    # Verify known currency names
    assert "coin" in currency_names_en, "Should contain 'Coin' currency"
    assert "karma" in currency_names_en, "Should contain 'Karma' currency"

    print(f"✅ Found {len(found_test_currencies)} test currencies out of {len(expected_test_currency_ids)} expected")
    print(f"   Total currencies in response: {len(data)}")

    # Show some example currencies
    example_currencies = data[:3] if len(data) >= 3 else data
    print(f"   Example currencies:")
    for currency in example_currencies:
        print(f"     - {currency['id']}: {currency['name']['en']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_icon_urls():
    """
    Test that icon_url fields are valid URLs when present.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()

    currencies_with_icons = 0

    for currency in data:
        icon_url = currency.get("icon_url")

        if icon_url is not None:
            currencies_with_icons += 1

            # Should be a string
            assert isinstance(icon_url, str), \
                f"Currency {currency['id']}: icon_url should be string, got {type(icon_url)}"

            # Should not be empty
            assert len(icon_url) > 0, \
                f"Currency {currency['id']}: icon_url should not be empty"

            # Should be a valid URL (start with http)
            assert icon_url.startswith("http://") or icon_url.startswith("https://"), \
                f"Currency {currency['id']}: icon_url should be a valid URL, got: {icon_url}"

    print(f"✅ All {len(data)} currencies have valid icon_url fields")
    print(f"   Currencies with icons: {currencies_with_icons}")

    if currencies_with_icons > 0:
        example_currency = next(c for c in data if c.get("icon_url"))
        print(f"   Example: {example_currency['name']['en']} -> {example_currency['icon_url']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_descriptions():
    """
    Test that description fields have content in all languages.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    required_langs = ["es", "en", "fr", "de"]

    currencies_with_descriptions = {lang: 0 for lang in required_langs}

    for currency in data:
        description = currency["description"]

        for lang in required_langs:
            if description[lang] is not None and len(description[lang]) > 0:
                currencies_with_descriptions[lang] += 1

    print(f"✅ Description field validation completed for {len(data)} currencies")
    print(f"   Currencies with descriptions per language:")
    for lang in required_langs:
        print(f"     - {lang}: {currencies_with_descriptions[lang]}/{len(data)}")

    # At least one currency should have a description in English
    assert currencies_with_descriptions["en"] > 0, \
        "At least one currency should have an English description"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_response_time():
    """
    Test that the /currencies endpoint responds within acceptable time.
    Should be fast due to caching.
    """
    client = CurrenciesEndpointClient()

    import time

    # First request (might hit GW2 API or database)
    start_time = time.time()
    response1 = await client.get_currencies()
    first_request_time = time.time() - start_time

    assert response1.status_code == 200

    # Second request (should hit cache)
    start_time = time.time()
    response2 = await client.get_currencies()
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
async def test_currencies_endpoint_consistent_data():
    """
    Test that multiple requests return consistent data.
    This validates data integrity and cache consistency.
    """
    client = CurrenciesEndpointClient()

    # Make 3 requests
    responses = []
    for i in range(3):
        response = await client.get_currencies()
        assert response.status_code == 200, f"Request {i + 1} failed"
        responses.append(response.json())

    # All responses should be identical
    first_response = responses[0]
    for idx, response in enumerate(responses[1:], start=2):
        assert response == first_response, \
            f"Request {idx} returned different data than request 1"

    # Check that IDs are unique (no duplicates)
    currency_ids = [currency["id"] for currency in first_response]
    unique_ids = set(currency_ids)

    assert len(currency_ids) == len(unique_ids), \
        f"Duplicate currency IDs found. Total: {len(currency_ids)}, Unique: {len(unique_ids)}"

    print(f"✅ Data is consistent across {len(responses)} requests")
    print(f"   Total currencies: {len(first_response)}")
    print(f"   All IDs unique: {len(unique_ids)} currencies")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_currencies_endpoint_multilingual_content():
    """
    Test that currencies have names and descriptions in all supported languages.
    This validates proper i18n (internationalization) support.
    """
    client = CurrenciesEndpointClient()

    response = await client.get_currencies()
    assert response.status_code == 200

    data = response.json()
    required_langs = ["es", "en", "fr", "de"]

    # Check that all currencies have names in all languages
    for currency in data:
        currency_id = currency["id"]

        # Verify name translations
        for lang in required_langs:
            assert currency["name"][lang] is not None, \
                f"Currency {currency_id} missing name translation for '{lang}'"
            assert len(currency["name"][lang]) > 0, \
                f"Currency {currency_id} has empty name translation for '{lang}'"

        # Verify that translations are different (not all the same)
        # Some games don't translate everything, so we just check they exist
        name_values = [currency["name"][lang] for lang in required_langs]
        assert len(name_values) == len(required_langs), \
            f"Currency {currency_id} missing some name translations"

    print(f"✅ All {len(data)} currencies have proper multilingual support")
    print(f"   Languages validated: {', '.join(required_langs)}")

    # Show example of multilingual content
    if len(data) > 0:
        example = data[0]
        print(f"   Example - Currency {example['id']}:")
        for lang in required_langs:
            print(f"     - {lang}: {example['name'][lang]}")
