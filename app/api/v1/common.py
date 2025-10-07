import httpx
from fastapi import APIRouter, Response, HTTPException
from fastapi.params import Header, Depends
from sqlalchemy.orm import Session

from app.db.dependency import get_db
from app.db.model import ApiKeys
from app.gw2.client import GW2Client

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/status", summary="Health Check", response_description="Service is alive")
def status():
    """
    Health check endpoint to verify if the service is running.
    :return:
    - 200 OK with "alive" message if the service is running.
    - 500 Internal Server Error if the service is down.
    """

    return Response(content="alive", media_type="text/plain", status_code=200)


@router.get("/tokeninfo", summary="Provides info about the API key", response_description="API Key info")
def check_token_info(
        authorization: str = Header(..., description="Authorization header: Bearer <API_KEY>"),
        db: Session = Depends(get_db)):
    """
    Validates the provided API key and retrieves its information.
    If the key is not found in the local database, it checks with the Guild Wars 2 API.
    If valid, the key is stored in the local database for future requests.
    :param authorization:
    :param db:
    :return:
    - 200 OK with API key information if the key is valid.
    - 400 Bad Request if the authorization header format is invalid.
    - 401 Unauthorized if the API key is missing or invalid.
    - 403 Forbidden if the API key is unauthorized.
    - 503 Service Unavailable if there is a connection failure to the Guild Wars 2 API.
    - 500 Internal Server Error for any other unexpected errors.
    """

    try:
        token = _split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token_info = db.query(ApiKeys).filter(ApiKeys.api_key == token).first()

    # No token found in DB -> check if it's valid with GW2 API
    if token_info is None:
        gw2 = GW2Client(api_key=token)
        token_info = _get_token_info_from_api(gw2)
        if token_info and token_info["permissions"] is not None:
            # Store the valid token in the database
            new_api_key = ApiKeys(
                api_key=token,
                permissions=token_info.get("permissions", []),
                game_account_id=None
            )

            db.add(new_api_key)
            db.commit()
            db.refresh(new_api_key)
            token_info = new_api_key

    return token_info


def _split_bearer_token(authorization: str) -> str:
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
        return token
    except ValueError:
        raise ValueError("Invalid authorization header format")


def _get_token_info_from_api(gw2: GW2Client):
    try:
        return gw2.token_info()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail="Missing or invalid token.")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="Missing or unauthorized token.")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Conection failure: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
