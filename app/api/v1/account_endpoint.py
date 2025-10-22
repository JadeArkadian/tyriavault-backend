from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.account_response import AccountInfoResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.database.session import get_db
from app.services.services import validate_api_key, get_account_service

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/", summary="Account summary", response_description="Account details", response_model=AccountInfoResponse)
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="account", key_builder=cache_key_builder)
async def account_details(
        api_key_data: Annotated[dict, Depends(validate_api_key)],
        db: AsyncSession = Depends(get_db)
) -> AccountInfoResponse:
    # Get account service with the API key
    account_service = get_account_service(db, api_key_data["api_key"])

    # Fetch account details using the UUID from validated API key
    return await account_service.get_account_details(api_key_data["game_account_uuid"])
