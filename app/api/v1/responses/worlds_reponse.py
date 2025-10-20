from typing import Self

from pydantic import BaseModel

from app.db.model import Worlds


class WorldsResponse(BaseModel):
    id: int
    name: dict[str, str]

    @classmethod
    def map_response(cls, world: Worlds) -> Self:
        mapped = WorldsResponse(
            id=world.id,
            name={
                "es": world.name_es if world else None,
                "en": world.name_en if world else None,
                "fr": world.name_fr if world else None,
                "de": world.name_de if world else None
            }
        )
        return mapped