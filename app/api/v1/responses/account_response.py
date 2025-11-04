from datetime import datetime
from typing import Optional, Self
from uuid import UUID

from pydantic import BaseModel

from app.services.dtos.account_dto import AccountDTO


class AccountInfoResponse(BaseModel):
    uuid: UUID
    account_name: str
    creation_date: datetime
    fractal_level: int
    world_name: dict[str, Optional[str]]
    content_access: list[str]

    @classmethod
    def from_dto(cls, account: AccountDTO) -> Self:
        """Create an AccountInfoResponse from an AccountDTO."""
        return cls(
            uuid=account.uuid,
            account_name=account.account_name,
            creation_date=account.creation_date,
            fractal_level=account.fractal_level,
            content_access=account.content_access,
            world_name={
                "es": account.world_name_es,
                "en": account.world_name_en,
                "fr": account.world_name_fr,
                "de": account.world_name_de
            }
        )
