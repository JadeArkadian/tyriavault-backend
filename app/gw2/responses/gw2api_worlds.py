"""
GW2 API Worlds response model.
"""
from pydantic import BaseModel, Field


class GW2ApiWorld(BaseModel):
    """Response model for a single world from /worlds endpoint."""

    id: int = Field(..., description="The world ID")
    name: str = Field(..., description="The localized name of the world")
    population: str = Field(..., description="The population level (Low, Medium, High, VeryHigh, Full)")
