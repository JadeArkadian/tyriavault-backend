from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

from app.api.v1.responses.worlds_response import WorldsResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.services.services import get_worlds_service
from app.services.worlds_service import WorldsService

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("", summary="Provides info about worlds", response_description="Worlds info",
            response_model=list[WorldsResponse])
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="worlds", key_builder=cache_key_builder)
async def get_worlds(worlds_service: Annotated[WorldsService, Depends(get_worlds_service)]) -> list[WorldsResponse]:
    worlds_data = await worlds_service.get_all_worlds()
    return [WorldsResponse.map_response(world) for world in worlds_data]
