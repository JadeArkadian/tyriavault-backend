from typing import Self

from pydantic import BaseModel

from app.services.dtos.worlds_dto import WorldDTO


class WorldsResponse(BaseModel):
    id: int
    name: dict[str, str]

    @classmethod
    def from_dto(cls, world: WorldDTO) -> Self:
        """Create a WorldsResponse from a WorldDTO."""
        return cls(
            id=world.id,
            name={
                "es": world.name_es,
                "en": world.name_en,
                "fr": world.name_fr,
                "de": world.name_de
            }
        )
