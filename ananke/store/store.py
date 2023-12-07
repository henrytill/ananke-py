"""The store protocol."""
from typing import Any, Optional, Protocol

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
    ) -> None:
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


# pylint: disable=unnecessary-ellipsis, too-few-public-methods
class Reader(Protocol):
    "The reader protocol."

    def read(self) -> Any:
        "Reads."
        ...


# pylint: disable=unnecessary-ellipsis, too-few-public-methods
class Writer(Protocol):
    "The writer protocol."

    def write(self, writes: Any) -> None:
        "Writes."
        ...


# pylint: disable=unnecessary-ellipsis
class Store(Protocol):
    "The store protocol."

    def init(self, reader: Reader) -> None:
        """Initializes the store.

        Args:
            reader: The reader to use to initialize the store.
        """
        ...

    def put(self, entry: Entry) -> None:
        """Puts an entry into the store.

        Args:
            entry: The entry to put into the store.
        """
        ...

    def remove(self, entry: Entry) -> None:
        """Removes an entry from the store.

        Args:
            entry: The entry to remove from the store.
        """
        ...

    def query(self, query: Query) -> list[Entry]:
        """Queries the store.

        Args:
            query: The query to run.

        Returns:
            A list of entries that match the query.
        """
        ...

    def select_all(self) -> list[Entry]:
        """Returns all entries from the store.

        Returns:
            A list of entries.
        """
        ...

    def get_count(self) -> int:
        """Returns the count of all entries in the store.

        Returns:
            The count of all entries.
        """
        ...

    def get_count_of_key_id(self, key_id: KeyId) -> int:
        """Returns the count of entries for a specific key id.

        Args:
            key_id: The key id to count entries for.

        Returns:
            The count of entries for the key id.
        """
        ...

    def sync(self, writer: Writer) -> None:
        """Synchronizes the store.

        Args:
            writer: The writer to use to synchronize the store.
        """
        ...