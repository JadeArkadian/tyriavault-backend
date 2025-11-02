from typing import Self

from pydantic import BaseModel

from app.services.dtos.dyes_dto import DyeDTO


class DyesResponse(BaseModel):
    id: int
    name: dict[str, str]
    hexcolor: str

    @classmethod
    def from_dto(cls, dye: DyeDTO) -> Self:
        """Create a DyesResponse from a DyeDTO."""
        return cls(
            id=dye.id,
            name={
                "es": dye.name_es,
                "en": dye.name_en,
                "fr": dye.name_fr,
                "de": dye.name_de
            },
            hexcolor=dye.color
        )
