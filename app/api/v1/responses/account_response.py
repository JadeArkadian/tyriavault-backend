from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Self

from app.db.model import GameAccounts


class AccountInfoResponse(BaseModel):
    uuid: UUID
    account_name: str
    creation_date: datetime
    fractal_level: int
    last_modified: datetime
    world_name: dict[str, Optional[str]]
    content_access: List[str]

    @classmethod
    def map_response(cls, game_account: GameAccounts) -> Self:
        mapped = AccountInfoResponse(
            uuid=game_account.uuid,
            account_name=game_account.account_name,
            creation_date=game_account.creation_date,
            fractal_level=game_account.fractal_level,
            last_modified=game_account.last_modified,
            content_access=game_account.content_access,
            world_name={
                "es": game_account.world.name_es if game_account.world else None,
                "en": game_account.world.name_en if game_account.world else None,
                "fr": game_account.world.name_fr if game_account.world else None,
                "de": game_account.world.name_de if game_account.world else None
            }
        )
        return mapped
