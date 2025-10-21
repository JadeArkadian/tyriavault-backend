import asyncio

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi_cache.decorator import cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.currencies_response import CurrenciesResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.db.dependency import get_db
from app.db.model import Currencies
from app.gw2.client import GW2Client

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("/", summary="Provides info about currencies", response_description="Currencies info")
@cache(expire=settings.CACHE_TTL_SECONDS, namespace="currencies", key_builder=cache_key_builder)
async def get_currencies(db: AsyncSession = Depends(get_db)) -> list[CurrenciesResponse]:
    result = await db.execute(select(Currencies))
    currencies_info = result.scalars().all()

    # No currencies on DB? -> check if the token is valid with GW2 API
    if currencies_info is None or not currencies_info:
        gw2 = GW2Client()
        currencies_info_from_api = await get_currencies_info_from_api(gw2)
        if currencies_info_from_api is not None:
            # Store the currencies in the database
            currencies_info = []
            for currency in currencies_info_from_api:
                currency_obj = Currencies(**currency)
                db.add(currency_obj)
                currencies_info.append(currency_obj)
            await db.commit()

    return [CurrenciesResponse.map_response(currency) for currency in currencies_info]


async def get_currencies_info_from_api(gw2: GW2Client) -> list[dict]:
    try:
        results = await asyncio.gather(
            gw2.get_currencies(lang="en"),
            gw2.get_currencies(lang="es"),
            gw2.get_currencies(lang="de"),
            gw2.get_currencies(lang="fr")
        )

        combined_currencies = {}

        for lang, currencies in zip(["en", "es", "de", "fr"], results):
            for currency in currencies:
                currency_id = currency["id"]
                if currency_id not in combined_currencies:
                    combined_currencies[currency_id] = {"id": currency_id}
                combined_currencies[currency_id]["icon_url"] = currency["icon"]
                combined_currencies[currency_id][f"name_{lang}"] = currency["name"]
                combined_currencies[currency_id][f"description_{lang}"] = currency["description"]
        return list(combined_currencies.values())

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text) from e

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Connection failure: {str(e)}") from e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e
