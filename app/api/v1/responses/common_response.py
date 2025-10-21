from typing import List, Self

from pydantic import BaseModel


class TokenInfoResponse(BaseModel):
    api_key: str
    permissions: List[str]

    @classmethod
    def map_response(cls, token_info: dict, token: str) -> Self:
        try:
            return TokenInfoResponse(
                api_key=token,
                permissions=token_info.get("permissions", []))
        except KeyError as ke:
            raise ValueError(f"Missing required key in token_info: {ke.args[0]}") from ke
