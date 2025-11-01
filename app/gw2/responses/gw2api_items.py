"""
GW2 API Items response models.
Documentation: https://wiki.guildwars2.com/wiki/API:2/items
"""
from typing import Literal

from pydantic import BaseModel, Field


# ===========================
# Main Item Model
# ===========================

class GW2ApiItem(BaseModel):
    """Response model for a single item from /items endpoint."""

    # Required fields
    id: int = Field(..., description="The item ID")
    name: str = Field(..., description="The item name")
    type: Literal[
        "Armor", "Back", "Bag", "Consumable", "Container", "CraftingMaterial",
        "Gathering", "Gizmo", "JadeTechModule", "Key", "MiniPet", "PowerCore",
        "Relic", "Tool", "Trait", "Trinket", "Trophy", "UpgradeComponent",
        "Weapon"
    ] = Field(..., description="The item type")
    chat_link: str = Field(..., description="The chat link code")
    icon: str | None = Field(default=None, description="The full icon URL")

    # Optional common fields
    description: str | None = Field(default=None, description="The item description")
    rarity: Literal["Junk", "Basic", "Fine", "Masterwork", "Rare", "Exotic", "Ascended", "Legendary"] | None = Field(
        default=None, description="The item rarity"
    )
    level: int | None = Field(default=None, description="The required level")
    vendor_value: int | None = Field(default=None, description="The value in coins when selling to a vendor")
    default_skin: int | None = Field(default=None, description="The default skin ID")

    # Flags and restrictions
    flags: list[str] = Field(default_factory=list, description="Flags applying to the item")
    game_types: list[str] = Field(default_factory=list, description="Game types where the item is usable")
    restrictions: list[str] = Field(default_factory=list, description="Restrictions on the item")

    # Upgrade information
    upgrades_into: list[dict] | None = Field(default=None, description="Lists what items this item can be upgraded into")
    upgrades_from: list[dict] | None = Field(default=None, description="Lists what items this item can be upgraded from")

    # Details - Union of all possible detail types
    # TODO: Details are way too complex to do properly right now -> will be done later
    # See gw2api_items_details.py.wip for individual detail models
    """
    details: Union[
        ArmorDetails,
        WeaponDetails,
        TrinketDetails,
        BackDetails,
        ConsumableDetails,
        ContainerDetails,
        GatheringDetails,
        BagDetails,
        UpgradeComponentDetails,
        SalvageKitDetails,
        MiniatureDetails,
        dict,
        None
    ] = Field(default=None, description="Additional item details (type-specific)")
    """
