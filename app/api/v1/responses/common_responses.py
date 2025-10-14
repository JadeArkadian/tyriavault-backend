from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from typing_extensions import Self

from app.db.model import ApiKeys


class TokenInfoResponse(BaseModel):
    api_key: str
    permissions: List[str]
    last_time_checked: datetime
    game_account_uuid: Optional[UUID]

    @classmethod
    def map_response(cls, api_key: ApiKeys) -> Self:
        return TokenInfoResponse(
            api_key=api_key.api_key,
            permissions=api_key.permissions,
            last_time_checked=api_key.last_time_checked,
            game_account_uuid=api_key.game_account_uuid
        )



