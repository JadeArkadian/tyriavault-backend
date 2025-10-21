import httpx
import pytest
from fastapi import HTTPException

from app.core.utils import split_bearer_token, handle_gw2_api_error


# Test 1: Header Ok
def test_split_bearer_token_valid():
    token = "mi_token"
    header = f"Bearer {token}"
    assert split_bearer_token(header) == token


# Test 2: Bad scheme
def test_split_bearer_token_invalid_scheme():
    header = "Basic mi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Test 3: Incorrect format (no space)
def test_split_bearer_token_invalid_format():
    header = "Bearermi_token"
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Test 4: Empty header
def test_split_bearer_token_empty():
    header = ""
    with pytest.raises(ValueError) as exc:
        split_bearer_token(header)
    assert "Invalid authorization header format" in str(exc.value)


# Tests for handle_gw2_api_error

# Test 5: HTTPStatusError with 401 status code
def test_handle_gw2_api_error_401():
    request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
    response = httpx.Response(401, request=request, text="Unauthorized")
    error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing or invalid token."


# Test 6: HTTPStatusError with 403 status code
def test_handle_gw2_api_error_403():
    request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
    response = httpx.Response(403, request=request, text="Forbidden")
    error = httpx.HTTPStatusError("Forbidden", request=request, response=response)

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 403
    assert exc.value.detail == "Missing or unauthorized token."


# Test 7: HTTPStatusError with other status codes (404)
def test_handle_gw2_api_error_other_http_status():
    request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
    response = httpx.Response(404, request=request, text="Not Found")
    error = httpx.HTTPStatusError("Not Found", request=request, response=response)

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Not Found"


# Test 8: HTTPStatusError with 500 status code
def test_handle_gw2_api_error_500():
    request = httpx.Request("GET", "https://api.guildwars2.com/v2/account")
    response = httpx.Response(500, request=request, text="Internal Server Error")
    error = httpx.HTTPStatusError("Server Error", request=request, response=response)

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 500
    assert exc.value.detail == "Internal Server Error"


# Test 9: RequestError (connection failure)
def test_handle_gw2_api_error_request_error():
    error = httpx.RequestError("Connection timeout")

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 503
    assert "Connection failure:" in exc.value.detail
    assert "Connection timeout" in exc.value.detail


# Test 10: Generic Exception
def test_handle_gw2_api_error_generic_exception():
    error = Exception("Unexpected error occurred")

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 500
    assert "Internal error:" in exc.value.detail
    assert "Unexpected error occurred" in exc.value.detail


# Test 11: RequestError with different message
def test_handle_gw2_api_error_connection_refused():
    error = httpx.ConnectError("Connection refused")

    with pytest.raises(HTTPException) as exc:
        handle_gw2_api_error(error)
    assert exc.value.status_code == 503
    assert "Connection failure:" in exc.value.detail
    assert "Connection refused" in exc.value.detail
