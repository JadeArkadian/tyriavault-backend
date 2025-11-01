"""DTO for Wallet data transfer between layers."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.database.models import Wallet


@dataclass
class WalletItemDTO:
    """Data Transfer Object for Wallet item information."""

    currency_id: int
    amount: int
    # Currency information embedded
    currency_name_en: str
    currency_name_es: str
    currency_name_de: str
    currency_name_fr: str
    currency_description_en: Optional[str]
    currency_description_es: Optional[str]
    currency_description_de: Optional[str]
    currency_description_fr: Optional[str]
    currency_icon_url: Optional[str]

    @classmethod
    def from_orm_with_currency(cls, wallet_model, currency_model) -> "WalletItemDTO":
        """Create a WalletItemDTO from database models (Wallet + Currency)."""
        return cls(
            currency_id=wallet_model.currency_id,
            amount=wallet_model.amount or 0,
            currency_name_en=currency_model.name_en,
            currency_name_es=currency_model.name_es,
            currency_name_de=currency_model.name_de,
            currency_name_fr=currency_model.name_fr,
            currency_description_en=currency_model.description_en,
            currency_description_es=currency_model.description_es,
            currency_description_de=currency_model.description_de,
            currency_description_fr=currency_model.description_fr,
            currency_icon_url=currency_model.icon_url
        )

    @classmethod
    def from_api_with_currency(cls, api_wallet_entry, currency_model) -> "WalletItemDTO":
        """Create a WalletItemDTO from API data and currency model."""
        return cls(
            currency_id=api_wallet_entry.id,
            amount=api_wallet_entry.value,
            currency_name_en=currency_model.name_en,
            currency_name_es=currency_model.name_es,
            currency_name_de=currency_model.name_de,
            currency_name_fr=currency_model.name_fr,
            currency_description_en=currency_model.description_en,
            currency_description_es=currency_model.description_es,
            currency_description_de=currency_model.description_de,
            currency_description_fr=currency_model.description_fr,
            currency_icon_url=currency_model.icon_url
        )

    def to_wallet_orm(self, game_account_uuid: UUID):
        """Convert the DTO to a Wallet ORM model instance."""
        return Wallet(
            currency_id=self.currency_id,
            game_account_uuid=game_account_uuid,
            amount=self.amount
        )
