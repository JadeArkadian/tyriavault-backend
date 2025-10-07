from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import settings
from app.db.model import Base
from app.db.session import engine
from app.gw2.client import GW2Client

# Setting up FastApi and our services
api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)
api.include_router(api_router, prefix="/api/v1")

@api.on_event("startup")
def startup_event():
    print("Turn On")
    print(settings.DATABASE_URL)
    # creates tables if not present
    Base.metadata.create_all(bind=engine)
    gw2 = GW2Client(api_key=settings.GW2_API_KEY)
    test = gw2.get_account()
    print(test)
