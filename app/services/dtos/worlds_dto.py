"""DTO for World data transfer between layers."""
from dataclasses import dataclass

from app.database.models import Worlds


@dataclass
class WorldDTO:
    """Data Transfer Object for World information."""

    id: int
    name_en: str
    name_es: str
    name_de: str
    name_fr: str

    @classmethod
    def from_orm(cls, world_model: Worlds) -> "WorldDTO":
        """Create a WorldDTO from a database model."""
        return cls(
            id=world_model.id,
            name_en=world_model.name_en,
            name_es=world_model.name_es,
            name_de=world_model.name_de,
            name_fr=world_model.name_fr
        )

    def to_orm(self) -> Worlds:
        """Convert the DTO to an ORM model instance."""
        return Worlds(
            id=self.id,
            name_en=self.name_en,
            name_es=self.name_es,
            name_de=self.name_de,
            name_fr=self.name_fr
        )
