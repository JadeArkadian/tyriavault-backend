from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

from app.api.v1.responses.dyes_response import DyesResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.services.dyes_service import DyesService
from app.services.services import get_dyes_service

router = APIRouter(prefix="/dyes", tags=["dyes"])


@router.get("", summary="Provides info about dyes", response_description="Dyes info",
            response_model=list[DyesResponse])
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="dyes", key_builder=cache_key_builder)
async def get_dyes(dyes_service: Annotated[DyesService, Depends(get_dyes_service)]) -> list[DyesResponse]:
    dyes_data = await dyes_service.get_all_dyes()
    return [DyesResponse.map_response(dye) for dye in dyes_data]
