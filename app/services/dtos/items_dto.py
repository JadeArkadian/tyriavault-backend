"""DTO for Item data transfer between layers."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database.models import Items


@dataclass
class ItemDTO:
    """Data Transfer Object for Item information."""

    id: int
    name_en: str
    name_es: str
    name_de: str
    name_fr: str
    chat_link: str
    rarity_id: int
    description_en: Optional[str] = None
    description_es: Optional[str] = None
    description_de: Optional[str] = None
    description_fr: Optional[str] = None
    icon_url: Optional[str] = None
    item_type_id: Optional[int] = None
    required_level: Optional[int] = None
    vendor_value: Optional[int] = 0
    details: Optional[dict] = None
    flags: Optional[dict] = None
    last_fetched: Optional[datetime] = None
    added_timestamp: Optional[datetime] = None

    @classmethod
    def from_orm(cls, item_model: Items) -> "ItemDTO":
        """Create an ItemDTO from a database model."""
        return cls(
            id=item_model.id,
            name_en=item_model.name_en,
            name_es=item_model.name_es,
            name_de=item_model.name_de,
            name_fr=item_model.name_fr,
            chat_link=item_model.chat_link,
            rarity_id=item_model.rarity_id,
            description_en=item_model.description_en,
            description_es=item_model.description_es,
            description_de=item_model.description_de,
            description_fr=item_model.description_fr,
            icon_url=item_model.icon_url,
            item_type_id=item_model.item_type_id,
            required_level=item_model.required_level,
            vendor_value=item_model.vendor_value,
            details=item_model.details,
            flags=item_model.flags,
            last_fetched=item_model.last_fetched,
            added_timestamp=item_model.added_timestamp
        )

    def to_orm(self) -> Items:
        """Convert the DTO to an ORM model instance."""
        return Items(
            id=self.id,
            name_en=self.name_en,
            name_es=self.name_es,
            name_de=self.name_de,
            name_fr=self.name_fr,
            chat_link=self.chat_link,
            rarity_id=self.rarity_id,
            description_en=self.description_en,
            description_es=self.description_es,
            description_de=self.description_de,
            description_fr=self.description_fr,
            icon_url=self.icon_url,
            item_type_id=self.item_type_id,
            required_level=self.required_level,
            vendor_value=self.vendor_value,
            details=self.details,
            flags=self.flags
        )
