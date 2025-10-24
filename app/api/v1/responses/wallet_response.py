from typing import Optional, Self

from pydantic import BaseModel


class WalletItemResponse(BaseModel):
    currency_id: int
    amount: int
    currency_name: dict[str, str]
    currency_icon: Optional[str]
    currency_description: dict[str, str]

    @classmethod
    def map_response(cls, wallet_entry: dict, currency: dict) -> Self:
        mapped = WalletItemResponse(
            currency_id=wallet_entry['currency_id'],
            amount=wallet_entry['amount'] or 0,
            currency_name={
                "es": currency['name_es'],
                "en": currency['name_en'],
                "fr": currency['name_fr'],
                "de": currency['name_de']
            },
            currency_icon=currency['icon_url'],
            currency_description={
                "es": currency['description_es'],
                "en": currency['description_en'],
                "fr": currency['description_fr'],
                "de": currency['description_de']
            }
        )
        return mapped
