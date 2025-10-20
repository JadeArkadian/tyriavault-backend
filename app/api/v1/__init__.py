from fastapi import APIRouter

from . import common, worlds, account, currencies

api_router = APIRouter()
api_router.include_router(common.router)
api_router.include_router(account.router)
api_router.include_router(worlds.router)
api_router.include_router(currencies.router)
