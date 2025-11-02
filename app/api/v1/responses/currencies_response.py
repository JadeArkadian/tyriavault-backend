from typing import Self, Optional

from pydantic import BaseModel

from app.services.dtos.currencies_dto import CurrencyDTO


class CurrenciesResponse(BaseModel):
    id: int
    icon_url: Optional[str]
    name: dict[str, str]
    description: dict[str, str]

    @classmethod
    def from_dto(cls, currency: CurrencyDTO) -> Self:
        """Create a CurrenciesResponse from a CurrencyDTO."""
        return cls(
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
