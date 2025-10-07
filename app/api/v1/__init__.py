from fastapi import APIRouter
from . import common
from . import account

api_router = APIRouter()
api_router.include_router(common.router)
api_router.include_router(account.router)
