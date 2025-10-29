from typing import List, Self

from pydantic import BaseModel


class TokenInfoResponse(BaseModel):
    permissions: List[str]

    @classmethod
    def map_response(cls, token_info: dict) -> Self:
        try:
            return TokenInfoResponse(
                permissions=token_info.get("permissions", []))
        except KeyError as ke:
            raise ValueError(f"Missing required key in token_info: {ke.args[0]}") from ke
