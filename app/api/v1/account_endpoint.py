from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.responses.account_response import AccountInfoResponse
from app.api.v1.responses.wallet_response import WalletItemResponse
from app.core import settings
from app.core.cache import cache_key_builder
from app.database.session import get_db
from app.services.dtos.apikey_dto import ApiKeyDTO
from app.services.services import validate_api_key, get_account_service, get_wallet_service

router = APIRouter(prefix="/account", tags=["account"])


@router.get("", summary="Account summary", response_description="Account details", response_model=AccountInfoResponse)
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="account", key_builder=cache_key_builder)
async def account_details(
        api_key_data: Annotated[ApiKeyDTO, Depends(validate_api_key)],
        db: AsyncSession = Depends(get_db)
) -> AccountInfoResponse:
    # Get account service with the API key
    account_service = get_account_service(db, api_key_data.api_key)

    # Fetch account details using the UUID from validated API key
    account_dto = await account_service.get_account_details(api_key_data.game_account_uuid)

    # Convert DTO to response
    return AccountInfoResponse.from_dto(account_dto)


@router.get("/wallet", summary="Account wallet", response_description="Account wallet details", response_model=list[WalletItemResponse])
@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="account:wallet", key_builder=cache_key_builder)
async def account_wallet(
        api_key_data: Annotated[ApiKeyDTO, Depends(validate_api_key)],
        db: AsyncSession = Depends(get_db)
) -> list[WalletItemResponse]:
    # Get wallet service with the API key
    wallet_service = get_wallet_service(db, api_key_data.api_key)

    # Fetch wallet using the UUID from validated API key
    wallet_dtos = await wallet_service.get_wallet(api_key_data.game_account_uuid)

    # Convert DTOs to responses
    return [WalletItemResponse.from_dto(item) for item in wallet_dtos]
