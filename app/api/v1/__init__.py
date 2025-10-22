from fastapi import APIRouter

from . import common, worlds_endpoint, account, currencies_endpoint

api_router = APIRouter()
api_router.include_router(common.router)
api_router.include_router(account.router)
api_router.include_router(worlds_endpoint.router)
api_router.include_router(currencies_endpoint.router)
