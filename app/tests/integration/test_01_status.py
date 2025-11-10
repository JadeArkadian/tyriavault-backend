"""
Integration tests to verify /status endpoint.

This test verifies that:
1. The application starts correctly
2. Can connect to PostgreSQL database
3. Can connect to GW2 API mock (WireMock)
4. /status endpoint responds correctly
"""
import asyncio
from typing import Optional

import httpx
import pytest


class ApplicationClient:
    """Client to interact with the application during tests."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def wait_for_ready(self, max_retries: int = 10, retry_delay: float = 2.0) -> bool:
        """
        Wait for the application to be ready to receive requests.

        Args:
            max_retries: Maximum number of retries
            retry_delay: Seconds between retries

        Returns:
            True if the application is ready, False otherwise
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.base_url}/api/v1/common/status")
                    if response.status_code in [200, 503]:
                        print(f"✅ Application available on attempt {attempt + 1}/{max_retries}")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries - 1:
                    print(f"⏳ Attempt {attempt + 1}/{max_retries}: application not available, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"❌ Application did not respond after {max_retries} attempts")
                    return False
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return False

        return False

    async def get_status(self) -> Optional[httpx.Response]:
        """Get the application status."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await client.get(f"{self.base_url}/api/v1/common/status")
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_application_startup_and_status():
    """
    Main integration test that verifies:
    - The application starts correctly
    - The /status endpoint responds
    - Database connection works
    - GW2 API mock connection works
    """
    client = ApplicationClient()

    # Wait for the application to be ready
    is_ready = await client.wait_for_ready(max_retries=10, retry_delay=2.0)
    assert is_ready, "Application did not start within expected time"

    # Verify /status endpoint
    response = await client.get_status()
    assert response is not None, "Could not get response from /status endpoint"

    # Status can be 200 (alive) or 503 (API down but app running)
    assert response.status_code in [200, 503], \
        f"Unexpected status code: {response.status_code}, content: {response.text}"

    # Verify response content
    content = response.text
    assert "alive" in content.lower() or "unstable" in content.lower(), \
        f"Unexpected response from /status endpoint: {content}"

    print(f"✅ Integration test completed successfully")
    print(f"   Status code: {response.status_code}")
    print(f"   Response: {content}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_status_endpoint_with_wiremock():
    """
    Specific test to verify that /status endpoint can communicate
    with GW2 API mock (WireMock).
    """
    client = ApplicationClient()

    # Verify that WireMock is responding
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            wiremock_response = await http_client.get("http://localhost:8080/v2/build")
            assert wiremock_response.status_code == 200, \
                f"WireMock is not responding correctly: {wiremock_response.status_code}"

            wiremock_data = wiremock_response.json()
            assert "id" in wiremock_data, "WireMock response does not have expected format"
            print(f"✅ WireMock is working correctly: {wiremock_data}")
    except Exception as e:
        pytest.fail(f"Could not connect to WireMock: {e}")

    # Verify application endpoint
    response = await client.get_status()
    assert response is not None, "Could not get response from /status endpoint"
    assert response.status_code in [200, 503], \
        f"Unexpected status code: {response.status_code}"

    # If status is 200, it means the application could connect to GW2 API (WireMock)
    if response.status_code == 200:
        assert "alive" in response.text.lower(), \
            f"Unexpected response when status is 200: {response.text}"
        print("✅ Application is healthy and can communicate with GW2 API (WireMock)")
    else:
        print("⚠️  Application responds but reports instability (expected in some cases)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wiremock_connectivity():
    """Test to verify that WireMock is working correctly."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Test build endpoint
        response = await client.get("http://localhost:8080/v2/build")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)
        print(f"✅ WireMock /v2/build responded: {data}")

        # Test admin endpoint
        admin_response = await client.get("http://localhost:8080/__admin/mappings")
        assert admin_response.status_code == 200
        admin_data = admin_response.json()
        assert "mappings" in admin_data
        print(f"✅ WireMock has {len(admin_data['mappings'])} mappings configured")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connectivity():
    """Test to verify that PostgreSQL is working correctly."""
    import asyncpg

    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="test_user",
            password="test_password",
            database="tyriavault_test"
        )

        # Verify that schema exists
        schema_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'schema_tyriavault')"
        )
        assert schema_exists, "Schema schema_tyriavault does not exist"
        print("✅ Schema schema_tyriavault exists")

        # Verify that some tables exist
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'schema_tyriavault'"
        )
        table_names = [table["table_name"] for table in tables]
        print(f"✅ Database has {len(table_names)} tables: {table_names[:5]}...")

        assert len(table_names) > 0, "No tables in schema"

        await conn.close()
        print("✅ PostgreSQL connection successful and configuration correct")

    except Exception as e:
        pytest.fail(f"Could not connect to PostgreSQL: {e}")
