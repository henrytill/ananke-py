"""An abstract store."""
from abc import ABC, abstractmethod
from typing import NewType, Optional

from ..data import Description, Entry, EntryId, Identity, KeyId, Metadata


class Query:
    """A query for filtering entries.

    This class is used to filter entries in a store.

    It may be subclassed to add additional filtering capabilities.

    Attributes:
        entry_id: The entry id to filter by.
        description: The description to filter by.
        identity: The identity to filter by.
        meta: The metadata to filter by.
    """

    __entry_id: Optional[EntryId]
    __description: Optional[Description]
    __identity: Optional[Identity]
    __meta: Optional[Metadata]

    def __init__(
        self,
        entry_id: Optional[EntryId] = None,
        description: Optional[Description] = None,
        identity: Optional[Identity] = None,
        meta: Optional[Metadata] = None,
    ):
        self.__entry_id = entry_id
        self.__description = description
        self.__identity = identity
        self.__meta = meta

    @property
    def entry_id(self) -> Optional[EntryId]:
        """Returns the entry id."""
        return self.__entry_id

    @property
    def description(self) -> Optional[Description]:
        """Returns the description."""
        return self.__description

    @property
    def identity(self) -> Optional[Identity]:
        """Returns the identity."""
        return self.__identity

    @property
    def meta(self) -> Optional[Metadata]:
        """Returns the metadata."""
        return self.__meta


# pylint: disable=too-few-public-methods
class AbstractReader(ABC):
    """An abstract reader."""

    @abstractmethod
    def read(self) -> list[Entry]:
        """Reads."""


# pylint: disable=too-few-public-methods
class AbstractWriter(ABC):
    """An abstract writer."""

    @abstractmethod
    def write(self, entries: list[Entry]) -> None:
        """Writes."""


class AbstractStore(ABC):
    """An abstract store."""

    @abstractmethod
    def init(self, reader: AbstractReader) -> None:
        """Initializes the store."""

    @abstractmethod
    def put(self, entry: Entry) -> None:
        """Stores an entry."""

    @abstractmethod
    def remove(self, entry: Entry) -> None:
        """Removes an entry."""

    @abstractmethod
    def query(self, query: Query) -> list[Entry]:
        """Runs a query and returns a list of entries."""

    @abstractmethod
    def select_all(self) -> list[Entry]:
        """Returns all entries."""

    @abstractmethod
    def get_count(self) -> int:
        """Returns the count of all entries."""

    @abstractmethod
    def get_count_of_key_id(self, key_id: KeyId) -> int:
        """Returns the count of entries for a specific key id."""

    @abstractmethod
    def sync(self, writer: AbstractWriter) -> None:
        """Synchronizes the store."""


SchemaVersion = NewType('SchemaVersion', int)
"""Represents a schema version."""


class AbstractMigratableStore(AbstractStore):
    """A store that can be migrated to a newer schema version."""

    @abstractmethod
    def migrate(self, schema_version: SchemaVersion, key_id: KeyId) -> None:
        """Migrates the store to the latest schema version."""

    @abstractmethod
    def current_schema_version(self) -> SchemaVersion:
        """Returns the current schema version of the store."""
