import pytest

from app.core.utils import split_bearer_token


# Caso 1: Header Ok
def test_split_bearer_token_valid():
    token = "mi_token"
    header = f"Bearer {token}"
    assert split_bearer_token(header) == token


# Caso 2: Bad scheme
def test_split_bearer_token_invalid_scheme():
    header = "Basic mi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Caso 3: Incorrect format (no space)
def test_split_bearer_token_invalid_format():
    header = "Bearermi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Caso 4: Empty header
def test_split_bearer_token_empty():
    header = ""
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)
