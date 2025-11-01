from datetime import datetime
from typing import Optional, Self, Union
from uuid import UUID

from pydantic import BaseModel

from app.database.models import GameAccounts, Worlds
from app.gw2.responses import GW2ApiAccount


class AccountInfoResponse(BaseModel):
    uuid: UUID
    account_name: str
    creation_date: datetime
    fractal_level: int
    world_name: dict[str, Optional[str]]
    content_access: list[str]

    @classmethod
    def map_response(cls, game_account: Union[GW2ApiAccount, GameAccounts], world: Optional[Worlds]) -> Self:
        # Handle different account types
        if isinstance(game_account, GW2ApiAccount):
            uuid = UUID(game_account.id)
            account_name = game_account.name
            creation_date = game_account.created
            fractal_level = game_account.fractal_level or 1
            content_access = game_account.access or []
        else:  # GameAccounts
            uuid = game_account.uuid
            account_name = game_account.account_name
            creation_date = game_account.creation_date
            fractal_level = game_account.fractal_level
            content_access = game_account.content_access or []

        mapped = AccountInfoResponse(
            uuid=uuid,
            account_name=account_name,
            creation_date=creation_date,
            fractal_level=fractal_level,
            content_access=content_access,
            world_name={
                "es": world.name_es if world else None,
                "en": world.name_en if world else None,
                "fr": world.name_fr if world else None,
                "de": world.name_de if world else None
            }
        )
        return mapped
