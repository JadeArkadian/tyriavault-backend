from unittest.mock import patch

import pytest

from app.core.utils import split_bearer_token, get_db_url, chunked


# Header Ok
def test_split_bearer_token_valid():
    token = "mi_token"
    header = f"Bearer {token}"
    assert split_bearer_token(header) == token


# Bad scheme
def test_split_bearer_token_invalid_scheme():
    header = "Basic mi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Incorrect format (no space)
def test_split_bearer_token_invalid_format():
    header = "Bearermi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Empty header
def test_split_bearer_token_empty():
    header = ""
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Tests for get_db_url function


# PostgreSQL URL
@patch("app.core.utils.settings.DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
def test_get_db_url_postgresql():
    result = get_db_url()
    assert result == "postgresql+asyncpg://user:pass@localhost:5432/db"


# Postgres URL (alternative scheme)
@patch("app.core.utils.settings.DATABASE_URL", "postgres://user:pass@localhost:5432/db")
def test_get_db_url_postgres():
    result = get_db_url()
    assert result == "postgresql+asyncpg://user:pass@localhost:5432/db"


# Already has asyncpg driver
@patch("app.core.utils.settings.DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db")
def test_get_db_url_already_asyncpg():
    result = get_db_url()
    assert result == "postgresql+asyncpg://user:pass@localhost:5432/db"


# Unsupported database scheme
@patch("app.core.utils.settings.DATABASE_URL", "mysql://user:pass@localhost:3306/db")
def test_get_db_url_unsupported_scheme():
    with pytest.raises(ValueError) as exc:
        get_db_url()
    assert "Unsupported DATABASE_URL scheme" in str(exc.value)


# PostgreSQL with special characters in password
@patch("app.core.utils.settings.DATABASE_URL", "postgresql://user:p@ss:word@localhost:5432/db")
def test_get_db_url_postgresql_special_chars():
    result = get_db_url()
    assert result == "postgresql+asyncpg://user:p@ss:word@localhost:5432/db"


# Postgres with query parameters
@patch("app.core.utils.settings.DATABASE_URL", "postgres://user:pass@localhost:5432/db?sslmode=require")
def test_get_db_url_postgres_with_params():
    result = get_db_url()
    assert result == "postgresql+asyncpg://user:pass@localhost:5432/db?sslmode=require"


# Tests for rgb_to_hex function

# Black color (0, 0, 0)
def test_rgb_to_hex_black():
    from app.core.utils import rgb_to_hex
    result = rgb_to_hex((0, 0, 0))
    assert result == "#000000"


# White color (255, 255, 255)
def test_rgb_to_hex_white():
    from app.core.utils import rgb_to_hex
    result = rgb_to_hex((255, 255, 255))
    assert result == "#ffffff"


# Red color (255, 0, 0)
def test_rgb_to_hex_red():
    from app.core.utils import rgb_to_hex
    result = rgb_to_hex((255, 0, 0))
    assert result == "#ff0000"


# Tests for chunked function

def test_chunked_empty_list():
    result = list(chunked([], 3))
    assert result == []


def test_chunked_chunk_size_greater_than_list():
    items = [1, 2]
    result = list(chunked(items, 5))
    assert result == [[1, 2]]


def test_chunked_chunk_size_one():
    items = [1, 2, 3]
    result = list(chunked(items, 1))
    assert result == [[1], [2], [3]]


def test_chunked_chunk_size_equals_list_length():
    items = [1, 2, 3]
    result = list(chunked(items, 3))
    assert result == [[1, 2, 3]]


def test_chunked_chunk_size_not_divisor():
    items = [1, 2, 3, 4, 5]
    result = list(chunked(items, 2))
    assert result == [[1, 2], [3, 4], [5]]


def test_chunked_chunk_size_divisor():
    items = [1, 2, 3, 4]
    result = list(chunked(items, 2))
    assert result == [[1, 2], [3, 4]]
