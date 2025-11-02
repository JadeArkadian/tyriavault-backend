"""DTO for ApiKey data transfer between layers."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class ApiKeyDTO:
    """Data Transfer Object for API Key information."""

    api_key: str
    permissions: list[str]
    game_account_uuid: UUID
    # Optional account name (for validation response)
    account_name: Optional[str] = None

    @classmethod
    def from_orm(cls, apikey_model) -> "ApiKeyDTO":
        """Create an ApiKeyDTO from a database model."""
        return cls(
            api_key=apikey_model.api_key,
            permissions=apikey_model.permissions or [],
            game_account_uuid=apikey_model.game_account_uuid
        )

    @classmethod
    def from_validation(cls, api_key: str, permissions: list[str], account_uuid: UUID, account_name: str) -> "ApiKeyDTO":
        """Create an ApiKeyDTO from validation process."""
        return cls(
            api_key=api_key,
            permissions=permissions,
            game_account_uuid=account_uuid,
            account_name=account_name
        )
