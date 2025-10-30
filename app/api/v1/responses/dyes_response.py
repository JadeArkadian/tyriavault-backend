from typing import Self

from pydantic import BaseModel


class DyesResponse(BaseModel):
    id: int
    name: dict[str, str]
    hexcolor: str

    @classmethod
    def map_response(cls, dye: dict) -> Self:
        mapped = DyesResponse(
            id=dye['id'],
            name={
                "es": dye['name_es'],
                "en": dye['name_en'],
                "fr": dye['name_fr'],
                "de": dye['name_de']
            },
            hexcolor=dye['color']
        )
        return mapped
