from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Self


class AccountInfoResponse(BaseModel):
    uuid: UUID
    account_name: str
    creation_date: datetime
    fractal_level: int
    world_name: dict[str, Optional[str]]
    content_access: List[str]

    @classmethod
    def map_response(cls, game_account: dict, world_info: dict) -> Self:
        mapped = AccountInfoResponse(
            uuid=game_account['id'],
            account_name=game_account['name'],
            creation_date=game_account['created'],
            fractal_level=game_account['fractal_level'],
            content_access=game_account['access'],
            world_name={
                "es": world_info['name_es'] if world_info else None,
                "en": world_info['name_en'] if world_info else None,
                "fr": world_info['name_fr'] if world_info else None,
                "de": world_info['name_de'] if world_info else None
            }
        )
        return mapped
