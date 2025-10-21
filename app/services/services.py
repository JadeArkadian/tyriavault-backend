from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.currencies_repository import CurrenciesRepository
from app.database.session import get_db
from app.gw2.client import GW2Client
from app.services.currencies_service import CurrenciesService


def get_currencies_service(db: AsyncSession = Depends(get_db)) -> CurrenciesService:
    repository = CurrenciesRepository(db)
    gw2_client = GW2Client()
    return CurrenciesService(repository, gw2_client)
