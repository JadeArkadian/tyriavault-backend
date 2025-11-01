"""DTO for Currency data transfer between layers."""
from dataclasses import dataclass
from typing import Optional

from app.database.models import Currencies


@dataclass
class CurrencyDTO:
    """Data Transfer Object for Currency information."""

    id: int
    name_en: str
    name_es: str
    name_de: str
    name_fr: str
    description_en: Optional[str]
    description_es: Optional[str]
    description_de: Optional[str]
    description_fr: Optional[str]
    icon_url: Optional[str]

    @classmethod
    def from_orm(cls, currency_model) -> "CurrencyDTO":
        """Create a CurrencyDTO from a database model."""
        return cls(
            id=currency_model.id,
            name_en=currency_model.name_en,
            name_es=currency_model.name_es,
            name_de=currency_model.name_de,
            name_fr=currency_model.name_fr,
            description_en=currency_model.description_en,
            description_es=currency_model.description_es,
            description_de=currency_model.description_de,
            description_fr=currency_model.description_fr,
            icon_url=currency_model.icon_url
        )

    def to_orm(self):
        """Convert the DTO to an ORM model instance."""
        return Currencies(
            id=self.id,
            name_en=self.name_en,
            name_es=self.name_es,
            name_de=self.name_de,
            name_fr=self.name_fr,
            description_en=self.description_en,
            description_es=self.description_es,
            description_de=self.description_de,
            description_fr=self.description_fr,
            icon_url=self.icon_url
        )
