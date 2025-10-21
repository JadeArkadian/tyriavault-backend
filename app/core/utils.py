from typing import NoReturn

import httpx
from fastapi import HTTPException


def split_bearer_token(authorization: str) -> str:
    """
    Extracts the Bearer token from an authorization header string.

    Args:
        authorization (str): The authorization header value, expected in the format 'Bearer <token>'.

    Returns:
        str: The extracted token string.

    Raises:
        ValueError: If the authentication scheme is not 'Bearer' or the header format is invalid.
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
        return token
    except ValueError:
        raise ValueError("Invalid authorization header format")


def handle_gw2_api_error(e: Exception) -> NoReturn:
    """
    Handles errors from GW2 API calls and raises appropriate HTTPExceptions.

    Args:
        e (Exception): The exception raised during the API call.

    Raises:
        HTTPException: With appropriate status code and detail message.
    """
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Missing or invalid token.")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="Missing or unauthorized token.")
        elif e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limited by GW2 API. Try again later.")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    elif isinstance(e, httpx.RequestError):
        raise HTTPException(status_code=503, detail=f"Connection failure: {e!s}")
    else:
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")
