"""
Internal data models for services.
These models represent data structures used internally by services to pass data between layers.
"""
from typing import Optional

from pydantic import BaseModel, Field


class CurrencyData(BaseModel):
    """Internal model representing a currency with all language variants."""

    id: int = Field(..., description="The currency ID")
    name_en: str = Field(..., description="Name in English")
    name_es: str = Field(..., description="Name in Spanish")
    name_de: str = Field(..., description="Name in German")
    name_fr: str = Field(..., description="Name in French")
    description_en: str = Field(..., description="Description in English")
    description_es: str = Field(..., description="Description in Spanish")
    description_de: str = Field(..., description="Description in German")
    description_fr: str = Field(..., description="Description in French")
    icon_url: Optional[str] = Field(None, description="URL to the currency's icon")
