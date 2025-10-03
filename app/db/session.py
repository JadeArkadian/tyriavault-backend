from sqlalchemy.orm import sessionmaker, declarative_base
from app.core import settings
from sqlalchemy import create_engine

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Dependency that provides a database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
