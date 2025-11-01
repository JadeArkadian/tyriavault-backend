"""DTO for Account data transfer between layers."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.database.models import GameAccounts, Worlds
from app.gw2.responses import GW2ApiAccount


@dataclass
class AccountDTO:
    """Data Transfer Object for Account information."""

    uuid: UUID
    account_name: str
    creation_date: datetime
    fractal_level: int
    world_id: Optional[int]
    content_access: list[str]
    # World information embedded (optional)
    world_name_en: Optional[str] = None
    world_name_es: Optional[str] = None
    world_name_de: Optional[str] = None
    world_name_fr: Optional[str] = None

    @classmethod
    def from_orm(cls, account_model: GameAccounts) -> "AccountDTO":
        """Create an AccountDTO from a database model."""
        return cls(
            uuid=account_model.uuid,
            account_name=account_model.account_name,
            creation_date=account_model.creation_date,
            fractal_level=account_model.fractal_level,
            world_id=account_model.world_id,
            content_access=account_model.content_access or []
        )

    @classmethod
    def from_orm_with_world(cls, account_model: GameAccounts, world_model: Worlds = None) -> "AccountDTO":
        """Create an AccountDTO from database models (Account + World)."""
        dto = cls.from_orm(account_model)

        if world_model:
            dto.world_name_en = world_model.name_en
            dto.world_name_es = world_model.name_es
            dto.world_name_de = world_model.name_de
            dto.world_name_fr = world_model.name_fr

        return dto

    @classmethod
    def from_api(cls, api_account: GW2ApiAccount) -> "AccountDTO":
        """Create an AccountDTO from GW2 API account data."""
        return cls(
            uuid=UUID(api_account.id),
            account_name=api_account.name,
            creation_date=api_account.created,
            fractal_level=api_account.fractal_level or 1,
            world_id=api_account.world,
            content_access=api_account.access or []
        )

    @classmethod
    def from_api_with_world(cls, api_account: GW2ApiAccount, world_model=None) -> "AccountDTO":
        """Create an AccountDTO from API data with world information."""
        dto = cls.from_api(api_account)

        if world_model:
            dto.world_name_en = world_model.name_en
            dto.world_name_es = world_model.name_es
            dto.world_name_de = world_model.name_de
            dto.world_name_fr = world_model.name_fr

        return dto

    def to_orm(self) -> GameAccounts:
        """Convert the DTO to an ORM model instance."""

        return GameAccounts(
            uuid=self.uuid,
            account_name=self.account_name,
            world_id=self.world_id,
            creation_date=self.creation_date,
            fractal_level=self.fractal_level,
            last_modified=datetime.now(timezone.utc),
            content_access=self.content_access,
            last_fetched=datetime.now(timezone.utc)
        )
