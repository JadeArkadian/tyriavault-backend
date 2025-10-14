from datetime import datetime
from typing import List
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
    world_name: dict[str, str]
    content_access: List[str]

    @classmethod
    def map_response(cls, game_account: GameAccounts) -> Self:
        mapped = AccountInfoResponse(
            uuid=game_account.uuid,
            account_name=game_account.account_name,
            creation_date=game_account.creation_date,
            fractal_level=game_account.fractal_level,
            last_modified=game_account.last_modified,
            content_access=game_account.content_access
        )

        world_name_mapped = {
            "es": mapped.world_name.name_es,
            "en": mapped.world_name.name_en,
            "fr": mapped.world_name.name_fr,
            "de": mapped.world_name.name_de
        }

        mapped.world_name = world_name_mapped
        return mapped




