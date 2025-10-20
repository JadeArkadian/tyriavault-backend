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
                "es": world.name_es,
                "en": world.name_en,
                "fr": world.name_fr,
                "de": world.name_de
            }
        )
        return mapped