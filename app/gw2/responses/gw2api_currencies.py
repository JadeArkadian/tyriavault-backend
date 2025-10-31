"""
GW2 API Currencies response model.
"""
from pydantic import BaseModel, Field


class GW2ApiCurrency(BaseModel):
    """Response model for a single currency from /currencies endpoint."""

    id: int = Field(..., description="The currency ID")
    name: str = Field(default="", description="The localized name of the currency")
    description: str = Field(default="", description="The localized description of the currency")
    order: int = Field(..., description="The sorting order for the currency")
    icon: str = Field(..., description="The URL to the currency's icon")
