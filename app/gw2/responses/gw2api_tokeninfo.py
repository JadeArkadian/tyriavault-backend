"""
GW2 API TokenInfo response model.
"""
from pydantic import BaseModel, Field


class GW2ApiTokenInfo(BaseModel):
    """Response model for /tokeninfo endpoint."""

    id: str = Field(..., description="The token ID")
    name: str = Field(..., description="The name given to the API key")
    permissions: list[str] = Field(default_factory=list, description="List of permissions granted to this API key")
