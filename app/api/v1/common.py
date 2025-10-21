from fastapi import APIRouter, Response, HTTPException, Header
from fastapi_cache.decorator import cache

from app.api.v1.responses.common_response import TokenInfoResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.core.utils import split_bearer_token, handle_gw2_api_error
from app.gw2.client import GW2Client

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/status", summary="Health Check", response_description="Service is alive")
def status() -> Response:
    return Response(content="alive", media_type="text/plain", status_code=200)


@router.get("/tokeninfo", summary="Provides info about the API key", response_description="API Key info")
@cache(expire=settings.CACHE_TTL_SECONDS, namespace="common", key_builder=cache_key_builder)
async def check_token_info(
        authorization: str = Header(..., description="Authorization header: Bearer <API_KEY>")) -> TokenInfoResponse:
    try:
        token = split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    gw2 = GW2Client(api_key=token)
    token_info_from_api = await get_token_info_from_api(gw2)

    return TokenInfoResponse.map_response(token_info_from_api)


async def get_token_info_from_api(gw2: GW2Client) -> dict:
    try:
        return await gw2.token_info()
    except Exception as e:
        handle_gw2_api_error(e)
