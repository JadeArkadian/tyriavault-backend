from typing import Annotated

from fastapi import APIRouter, Response, Depends
from fastapi_cache.decorator import cache

from app.api.v1.responses.tokeninfo_response import TokenInfoResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.services.health_service import HealthService
from app.services.services import validate_api_key, get_health_service

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/status", summary="Health Check", response_description="Service is alive")
async def status(health_service: Annotated[HealthService, Depends(get_health_service)]) -> Response:
    is_healthy = await health_service.check_gw2_api_status()
    if is_healthy:
        return Response(content="alive", media_type="text/plain", status_code=200)
    else:
        return Response(content="unstable: API down", media_type="text/plain", status_code=503)


@router.get("/tokeninfo", summary="Provides info about the API key", response_description="API Key info")
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="common", key_builder=cache_key_builder)
async def check_token_info(api_key_data: Annotated[dict, Depends(validate_api_key)]) -> TokenInfoResponse:
    return TokenInfoResponse.map_response(api_key_data)
