from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core import settings
from app.core.utils import get_db_url

# Ensure the URL uses asyncpg driver
engine = create_async_engine(get_db_url(), echo=settings.LOG_LEVEL == "DEBUG", pool_pre_ping=True,
                             pool_size=10, max_overflow=20)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
