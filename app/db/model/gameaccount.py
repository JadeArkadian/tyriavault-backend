from sqlalchemy import Column, Integer, String, DateTime, func

from app.db.base import Base


class GameAccount(Base):
    __tablename__ = "game_accounts"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    account_name = Column(String, unique=True, nullable=False, index=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    world = Column(String, index=True)
    email = Column(String, unique=True, index=True)
