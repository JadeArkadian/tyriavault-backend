"""
GW2 API Account response model.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class GW2ApiAccount(BaseModel):
    """Response model for /account endpoint."""

    id: str = Field(..., description="The unique account GUID")
    name: str = Field(..., description="The account name (name.1234)")
    age: int = Field(..., description="The age of the account in seconds")
    world: int | None = Field(default=None, description="The ID of the home world")
    guilds: list[str] = Field(default_factory=list, description="List of guild IDs the account is a member of")
    guild_leader: list[str] = Field(default_factory=list, description="List of guild IDs where the account is a leader")
    created: datetime = Field(..., description="ISO-8601 timestamp of when the account was created")
    access: list[str] = Field(default_factory=list, description="List of expansions/content the account has access to")
    commander: bool = Field(default=False, description="Whether the account has a commander tag")
    fractal_level: int | None = Field(default=None, description="The account's fractal level")
    daily_ap: int | None = Field(default=None, description="The daily achievement points")
    monthly_ap: int | None = Field(default=None, description="The monthly achievement points")
    wvw_rank: int | None = Field(default=None, description="The account's WvW rank")
