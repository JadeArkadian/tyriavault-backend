from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Sequence

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository with minimal CRUD operations."""

    @abstractmethod
    async def get_by_id(self, _id: int) -> Optional[T]:
        """Get entity by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> Sequence[T]:
        """Get all entities."""
        ...

    @abstractmethod
    async def upsert(self, entity: T) -> T:
        """Insert or update entity (most common operation for syncing API data)."""
        ...
