from typing import List

from pydantic import BaseModel
from typing_extensions import Self


class TokenInfoResponse(BaseModel):
    api_key: str
    permissions: List[str]

    @classmethod
    def map_response(cls, token_info: dict) -> Self:
        try:
            return TokenInfoResponse(
                api_key=token_info["id"],
                permissions=token_info.get("permissions", []))
        except KeyError as ke:
            raise ValueError(f"Missing required key in token_info: {ke.args[0]}") from k
