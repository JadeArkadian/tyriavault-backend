from typing import List

from pydantic import BaseModel
from typing_extensions import Self


class TokenInfoResponse(BaseModel):
    api_key: str
    permissions: List[str]

    @classmethod
    def map_response(cls, api_key: dict) -> Self:
        return TokenInfoResponse(
            api_key=api_key['id'],
            permissions=api_key['permissions']
        )
