"""An abstract store."""
from abc import ABC, abstractmethod
from typing import Any, NewType

from ..data import Entry, KeyId
from .store import Query


# pylint: disable=too-few-public-methods
class AbstractReader(ABC):
    """An abstract reader."""

    @abstractmethod
    def read(self) -> Any:
        """Reads."""


# pylint: disable=too-few-public-methods
class AbstractWriter(ABC):
    """An abstract writer."""

    @abstractmethod
    def write(self, writes: Any) -> None:
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


SchemaVersion = NewType("SchemaVersion", int)
"""Represents a schema version."""


class AbstractMigratableStore(AbstractStore):
    """A store that can be migrated to a newer schema version."""

    @abstractmethod
    def migrate(self, schema_version: SchemaVersion, key_id: KeyId) -> None:
        """Migrates the store to the latest schema version."""

    @abstractmethod
    def current_schema_version(self) -> SchemaVersion:
        """Returns the current schema version of the store."""
