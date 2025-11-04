from typing import List, Self

from pydantic import BaseModel

from app.services.dtos.apikey_dto import ApiKeyDTO


class TokenInfoResponse(BaseModel):
    permissions: List[str]

    @classmethod
    def from_dto(cls, apikey: ApiKeyDTO) -> Self:
        """Create a TokenInfoResponse from an ApiKeyDTO."""
        return cls(permissions=apikey.permissions)
