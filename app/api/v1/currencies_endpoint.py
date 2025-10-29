from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

from app.api.v1.responses.currencies_response import CurrenciesResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.services.currencies_service import CurrenciesService
from app.services.services import get_currencies_service

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("", summary="Provides info about currencies", response_description="Currencies info",
            response_model=list[CurrenciesResponse])
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="currencies", key_builder=cache_key_builder)
async def get_currencies(currencies_service: Annotated[CurrenciesService, Depends(get_currencies_service)]) -> list[CurrenciesResponse]:
    currencies_data = await currencies_service.get_all_currencies()
    return [CurrenciesResponse.map_response(currency) for currency in currencies_data]
