from abc import ABC, abstractmethod
from typing import NewType, Optional

from ..data import Description, Entry, Id, Identity, KeyId, Metadata


class Query:
    """
    A query for filtering entries.

    Attributes:
        id: Optional ID to filter by.
        description: Optional description to filter by.
        identity: Optional identity to filter by.
        meta: Optional metadata to filter by.
    """

    id: Optional[Id]
    description: Optional[Description]
    identity: Optional[Identity]
    meta: Optional[Metadata]

    def __init__(
        self,
        id: Optional[Id] = None,
        description: Optional[Description] = None,
        identity: Optional[Identity] = None,
        meta: Optional[Metadata] = None,
    ):
        """
        Creates a query for filtering entries.

        Args:
            id: Optional ID to filter by.
            description: Optional description to filter by.
            identity: Optional identity to filter by.
            meta: Optional metadata to filter by.
        """
        self.id = id
        self.description = description
        self.identity = identity
        self.meta = meta


class AbstractStore(ABC):
    @abstractmethod
    def put(self, entry: Entry) -> None:
        """Stores an entry."""
        pass

    @abstractmethod
    def remove(self, entry: Entry) -> None:
        """Removes an entry."""
        pass

    @abstractmethod
    def query(self, query: Query) -> list[Entry]:
        """Runs a query and returns a list of entries."""
        pass

    @abstractmethod
    def select_all(self) -> list[Entry]:
        """Returns all entries."""
        pass

    @abstractmethod
    def get_count(self) -> int:
        """Returns the count of all entries."""
        pass

    @abstractmethod
    def get_count_of_key_id(self, key_id: KeyId) -> int:
        """Returns the count of entries for a specific key id."""
        pass


SchemaVersion = NewType('SchemaVersion', int)
"""Represents a schema version."""


class AbstractMigratableStore(AbstractStore):
    @abstractmethod
    def migrate(self, schema_version: SchemaVersion, key_id: KeyId) -> None:
        pass

    @abstractmethod
    def current_schema_version(self) -> SchemaVersion:
        pass
