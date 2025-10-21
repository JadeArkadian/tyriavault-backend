import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.params import Header
from fastapi_cache.decorator import cache

from app.api.v1.responses.account_response import AccountInfoResponse
from app.api.v1.worlds import get_worlds_info_from_api
from app.core import settings
from app.core.cache import cache_key_builder
from app.core.utils import split_bearer_token, handle_gw2_api_error
from app.gw2.client import GW2Client

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/", summary="Account summary", response_description="Account details")
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="account", key_builder=cache_key_builder)
async def account_details(authorization: str = Header(...,
                                                      description="Authorization header: Bearer <API_KEY>")) -> AccountInfoResponse:
    try:
        token = split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    gw2 = GW2Client(api_key=token)

    results = await asyncio.gather(
        get_account_info_from_api(gw2),
        get_worlds_info_from_api(gw2),
    )

    game_account_info_from_api, worlds_info_from_api = results

    worlds_by_id = {w["id"]: w for w in worlds_info_from_api}
    world_info = worlds_by_id.get(game_account_info_from_api["world"])

    return AccountInfoResponse.map_response(game_account_info_from_api, world_info)


async def get_account_info_from_api(gw2: GW2Client):
    try:
        return await gw2.get_account()
    except Exception as e:
        handle_gw2_api_error(e)
