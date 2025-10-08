from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core import settings

engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
