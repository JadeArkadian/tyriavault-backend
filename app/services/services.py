from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends, Header
from fastapi_cache.decorator import cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.core.cache import cache_key_builder
from app.core.logging import logger
from app.core.utils import split_bearer_token
from app.database.repositories.account_repository import AccountRepository
from app.database.repositories.apikeys_repository import ApikeysRepository
from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.repositories.wallet_repository import WalletRepository
from app.database.repositories.worlds_repository import WorldsRepository
from app.database.session import get_db
from app.gw2.client import GW2Client
from app.services.account_service import AccountService
from app.services.apikey_service import ApiKeyService
from app.services.currencies_service import CurrenciesService
from app.services.health_service import HealthService
from app.services.wallet_service import WalletService
from app.services.worlds_service import WorldsService


def get_health_service() -> HealthService:
    gw2_client = GW2Client()
    return HealthService(gw2_client)


def get_api_key_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ApiKeyService:
    api_keys_repo = ApikeysRepository(db)
    worlds_repo = WorldsRepository(db)
    return ApiKeyService(api_keys_repo, worlds_repo)


def get_currencies_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CurrenciesService:
    repository = CurrenciesRepository(db)
    gw2_client = GW2Client()
    return CurrenciesService(repository, gw2_client)


def get_worlds_service(db: Annotated[AsyncSession, Depends(get_db)]) -> WorldsService:
    repository = WorldsRepository(db)
    gw2_client = GW2Client()
    return WorldsService(repository, gw2_client)


def get_account_service(db: Annotated[AsyncSession, Depends(get_db)], apikey: str) -> AccountService:
    account_repository = AccountRepository(db)
    worlds_repository = WorldsRepository(db)
    gw2_client = GW2Client(apikey)
    return AccountService(account_repository, worlds_repository, gw2_client)


def get_wallet_service(db: Annotated[AsyncSession, Depends(get_db)], apikey: str) -> WalletService:
    wallet_repository = WalletRepository(db)
    currencies_repository = CurrenciesRepository(db)
    gw2_client = GW2Client(apikey)
    return WalletService(wallet_repository, currencies_repository, gw2_client)


@cache(expire=settings.CACHE_TTL_NORMAL_SECONDS, namespace="apikey", key_builder=cache_key_builder)
async def validate_api_key(
        authorization: str = Header(..., description="Authorization header: Bearer <API_KEY>"),
        api_key_service: ApiKeyService = Depends(get_api_key_service)) -> dict:
    """
    Dependency to validate API key from Authorization header and return its data.
    Use it in endpoints that require API key authentication.
    Raises HTTPException if API key is invalid or not registered.
    """

    try:
        # Extract API key from Bearer token
        api_key = split_bearer_token(authorization)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        logger.debug("Validating API key...")
        # Check if API key exists in DB
        api_key_data = await api_key_service.get_apikey_data_from_db(api_key)

        # First time using this API key? -> Register it
        if not api_key_data:
            api_key_data = await api_key_service.validate_and_register(api_key)

        return api_key_data

    except RuntimeError as e:
        # World not found or other validation errors
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        # Invalid API key or GW2 API errors
        raise HTTPException(status_code=401, detail=f"Invalid API key: {str(e)}") from e
