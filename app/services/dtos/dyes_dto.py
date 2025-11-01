"""DTO for Dye data transfer between layers."""
from dataclasses import dataclass

from app.database.models import Dyes


@dataclass
class DyeDTO:
    """Data Transfer Object for Dye information."""

    id: int
    name_en: str
    name_es: str
    name_de: str
    name_fr: str
    color: str

    @classmethod
    def from_orm(cls, dye_model) -> "DyeDTO":
        """Create a DyeDTO from a database model."""
        return cls(
            id=dye_model.id,
            name_en=dye_model.name_en,
            name_es=dye_model.name_es,
            name_de=dye_model.name_de,
            name_fr=dye_model.name_fr,
            color=dye_model.color
        )

    def to_orm(self):
        """Convert the DTO to an ORM model instance."""
        return Dyes(
            id=self.id,
            name_en=self.name_en,
            name_es=self.name_es,
            name_de=self.name_de,
            name_fr=self.name_fr,
            color=self.color
        )
