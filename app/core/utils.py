from typing import Any, Generator

from app.core import settings
from app.database.seeding.seed_data import RARITIES_DATA, ITEM_TYPES_DATA


def map_rarity_to_id(rarity: str | None) -> int:
    """Map GW2 rarity string to database rarity ID using seed data."""
    if not rarity:
        return 2  # Default to Basic

    # Build mapping from seed data
    for rarity_model in RARITIES_DATA:
        if rarity_model.name_en == rarity:
            return rarity_model.id

    return 2  # Default to Basic if not found


def map_type_to_id(item_type: str | None) -> int:
    """Map GW2 item type string to database item_type ID using seed data."""
    if not item_type:
        return 0  # Default to Unknown

    # Build mapping from seed data
    for type_model in ITEM_TYPES_DATA:
        if type_model.name_en == item_type:
            return type_model.id

    return 0  # Default to Unknown if not found


def chunked(items: list[Any], chunk_size: int) -> Generator[list[Any], Any, None]:
    """
    Splits a list of items into smaller chunks of a specified size.

    Args:
        items (list[Any]): The list of items to be chunked.
        chunk_size (int): The size of each chunk.

    Yields:
        list[Any]: A chunk of the original list.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def rgb_to_hex(rgb: tuple[int, int, int] | list[int]) -> str:
    """
    Converts an RGB color tuple or list to a hexadecimal color string.

    Args:
        rgb (tuple[int, int, int] | list[int]): A tuple or list containing the red, green, and blue components (0-255).

    Returns:
        str: The hexadecimal color string in the format '#RRGGBB'.
    """
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def get_db_url() -> str:
    """
    Ensures the DATABASE_URL uses the asyncpg driver for PostgreSQL.

    Returns:
        str: The modified DATABASE_URL with asyncpg driver.

    Raises:
        ValueError: If the DATABASE_URL scheme is unsupported.
    """
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif not db_url.startswith("postgresql+asyncpg://"):
        raise ValueError(f"Unsupported DATABASE_URL scheme")
    return db_url


def split_bearer_token(authorization: str) -> str:
    """
    Extracts the Bearer token from an authorization header string.

    Args:
        authorization (str): The authorization header value, expected in the format 'Bearer <token>'.

    Returns:
        str: The extracted token string.

    Raises:
        ValueError: If the authentication scheme is not 'Bearer' or the header format is invalid.
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
        return token
    except ValueError:
        raise ValueError("Invalid authorization header format")
