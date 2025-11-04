from typing import Optional, Self

from pydantic import BaseModel

from app.services.dtos.wallet_dto import WalletItemDTO


class WalletItemResponse(BaseModel):
    currency_id: int
    amount: int
    currency_name: dict[str, str]
    currency_icon: Optional[str]
    currency_description: dict[str, Optional[str]]

    @classmethod
    def from_dto(cls, wallet_item: WalletItemDTO) -> Self:
        """Create a WalletItemResponse from a WalletItemDTO."""
        return cls(
            currency_id=wallet_item.currency_id,
            amount=wallet_item.amount,
            currency_name={
                "es": wallet_item.currency_name_es,
                "en": wallet_item.currency_name_en,
                "fr": wallet_item.currency_name_fr,
                "de": wallet_item.currency_name_de
            },
            currency_icon=wallet_item.currency_icon_url,
            currency_description={
                "es": wallet_item.currency_description_es,
                "en": wallet_item.currency_description_en,
                "fr": wallet_item.currency_description_fr,
                "de": wallet_item.currency_description_de
            }
        )
