"""
GW2 API Colors response model.
"""
from pydantic import BaseModel, Field


class MaterialColor(BaseModel):
    """Color information for a specific material type."""

    brightness: int = Field(..., description="Brightness modifier")
    contrast: float = Field(..., description="Contrast multiplier")
    hue: int = Field(..., description="Hue in HSL colorspace")
    saturation: float = Field(..., description="Saturation multiplier")
    lightness: float = Field(..., description="Lightness multiplier")
    rgb: list[int] = Field(..., description="RGB values [red, green, blue]")


class GW2ApiColor(BaseModel):
    """Response model for a single color/dye from /colors endpoint."""

    id: int = Field(..., description="The color ID")
    name: str = Field(..., description="The localized name of the color")
    base_rgb: list[int] = Field(..., description="The base RGB values [red, green, blue]")
    cloth: MaterialColor = Field(..., description="Detailed information on its appearance when applied on cloth armor")
    leather: MaterialColor = Field(..., description="Detailed information on its appearance when applied on leather armor")
    metal: MaterialColor = Field(..., description="Detailed information on its appearance when applied on metal armor")
    fur: MaterialColor | None = Field(default=None,
                                      description="Detailed information on its appearance when applied on fur armor (conditional)")
    item: int | None = Field(default=None, description="The item ID of the dye")
    categories: list[str] = Field(default_factory=list, description="The categories of the color")
