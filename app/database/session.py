from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core import settings

engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
                             echo=settings.LOG_LEVEL == "DEBUG", pool_pre_ping=True,
                             pool_size=10, max_overflow=20)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
