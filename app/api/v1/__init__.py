from fastapi import APIRouter

from . import common_endpoint, worlds_endpoint, account_endpoint, currencies_endpoint

api_router = APIRouter()
api_router.include_router(common_endpoint.router)
api_router.include_router(account_endpoint.router)
api_router.include_router(worlds_endpoint.router)
api_router.include_router(currencies_endpoint.router)
