from fastapi import APIRouter
from . import common

api_router = APIRouter()
api_router.include_router(common.router)