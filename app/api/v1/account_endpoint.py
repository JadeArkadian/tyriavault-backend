from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_cache.decorator import cache

from app.core import settings
from app.core.cache import cache_key_builder
from app.services.services import validate_api_key

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/", summary="Account summary", response_description="Account details")
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="account", key_builder=cache_key_builder)
async def account_details(api_key_data: dict = Depends(validate_api_key)):
    # TODO: implement account service to fetch more details if needed
    return api_key_data
