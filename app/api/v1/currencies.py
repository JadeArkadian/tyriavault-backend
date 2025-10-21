import asyncio

from fastapi import APIRouter
from fastapi_cache.decorator import cache

from app.api.v1.responses.currencies_response import CurrenciesResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.core.utils import handle_gw2_api_error
from app.gw2.client import GW2Client

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("/", summary="Provides info about currencies", response_description="Currencies info")
@cache(expire=settings.CACHE_TTL_SECONDS, namespace="currencies", key_builder=cache_key_builder)
async def get_currencies() -> list[CurrenciesResponse]:
    gw2 = GW2Client()
    currencies_info_from_api = await get_currencies_info_from_api(gw2)

    return [CurrenciesResponse.map_response(currency) for currency in currencies_info_from_api]


async def get_currencies_info_from_api(gw2: GW2Client) -> list[dict]:
    try:
        results = await asyncio.gather(
            gw2.get_currencies(lang="en"),
            gw2.get_currencies(lang="es"),
            gw2.get_currencies(lang="de"),
            gw2.get_currencies(lang="fr")
        )

        combined_currencies = {}

        for lang, currencies in zip(["en", "es", "de", "fr"], results, strict=True):
            for currency in currencies:
                currency_id = currency["id"]
                if currency_id not in combined_currencies:
                    combined_currencies[currency_id] = {"id": currency_id}
                    combined_currencies[currency_id]["icon_url"] = currency["icon"]
                combined_currencies[currency_id][f"name_{lang}"] = currency["name"]
                combined_currencies[currency_id][f"description_{lang}"] = currency["description"]
        return list(combined_currencies.values())
    except Exception as e:
        handle_gw2_api_error(e)
