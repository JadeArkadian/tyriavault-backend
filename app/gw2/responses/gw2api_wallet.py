"""
GW2 API Wallet response model.
"""
from pydantic import BaseModel, Field


class GW2ApiWalletEntry(BaseModel):
    """Response model for a single wallet entry from /account/wallet endpoint."""

    id: int = Field(..., description="The currency ID")
    value: int = Field(..., description="The amount of this currency in the wallet")
