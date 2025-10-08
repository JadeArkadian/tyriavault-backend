from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.db.model import Base
from app.db.session import engine

# Setting up FastApi and our services
api = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
)

origins = [settings.FRONTEND_URL]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

api.include_router(api_router, prefix="/api/v1")


@api.on_event("startup")
def startup_event():
    print("Turn On")
    print(settings.DATABASE_URL)
    # creates tables if not present
    Base.metadata.create_all(bind=engine)
