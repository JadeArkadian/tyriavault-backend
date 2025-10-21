from typing import Self, Optional
from pydantic import BaseModel
from app.db.model import Currencies


class CurrenciesResponse(BaseModel):
    id: int
    icon_url: Optional[str]
    name: dict[str, str]
    description: dict[str, str]

    @classmethod
    def map_response(cls, currency: Currencies) -> Self:
        mapped = CurrenciesResponse(
            id=currency.id,
            icon_url=currency.icon_url,
            name={
                "es": currency.name_es,
                "en": currency.name_en,
                "fr": currency.name_fr,
                "de": currency.name_de
            },
            description={
                "es": currency.description_es,
                "en": currency.description_en,
                "fr": currency.description_fr,
                "de": currency.description_de
            }
        )
        return mapped