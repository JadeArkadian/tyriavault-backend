"""
Specific configuration for integration tests.
"""
import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running integration tests."""
    os.environ["ENV"] = "test"
    yield
    # Cleanup
    if "ENV" in os.environ:
        del os.environ["ENV"]
