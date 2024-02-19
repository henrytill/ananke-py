"""The main application module."""

from contextlib import AbstractContextManager
from types import TracebackType
from typing import Optional, Self, Tuple, Type

from .codec import Codec
from .data import Description, Entry, EntryId, Identity, Metadata, Plaintext, Timestamp
from .store import Query, Reader, Store, Writer


class Application(AbstractContextManager["Application"]):
    """The main application class."""

    store: Store
    reader: Reader
    writer: Writer
    codec: Codec[Plaintext]

    def __init__(
        self,
        store: Store,
        reader: Reader,
        writer: Writer,
        codec: Codec[Plaintext],
    ) -> None:
        self.store = store
        self.reader = reader
        self.writer = writer
        self.codec = codec

    def __enter__(self) -> Self:
        self.init()
        return self

    def __exit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        _exc_value: Optional[BaseException],
        _traceback: Optional[TracebackType],
    ) -> None:
        self.sync()

    def init(self) -> None:
        """Initialize the store."""
        self.store.init(self.reader)

    def sync(self) -> None:
        """Synchronize the store."""
        self.store.sync(self.writer)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity],
        maybe_meta: Optional[Metadata],
    ) -> None:
        """Add a new entry.

        Args:
            description: The description of the entry.
            plaintext: The plaintext of the entry.
            maybe_identity: The identity of the entry.
            maybe_meta: The metadata of the entry.
        """
        timestamp = Timestamp.now()
        entry_id = EntryId.generate(self.codec.key_id, timestamp, description, maybe_identity)
        ciphertext = self.codec.encode(plaintext)
        entry = Entry(
            entry_id=entry_id,
            key_id=self.codec.key_id,
            timestamp=timestamp,
            description=description,
            identity=maybe_identity,
            ciphertext=ciphertext,
            meta=maybe_meta,
        )
        self.store.put(entry)

    def lookup(
        self,
        description: Description,
        maybe_identity: Optional[Identity] = None,
    ) -> list[Tuple[Entry, Plaintext]]:
        """Lookup the plaintexts of the matching entries.

        Searches for entries that match the provided description and identity,
        and returns the plaintexts of the matching entries.

        Args:
            description: The description to search for.
            maybe_identity: The identity to search for.

        Returns:
            A list of the matching entries and their corresponding plaintexts.
        """
        query = Query(description=description, identity=maybe_identity)
        return [(result, self.codec.decode(result.ciphertext)) for result in self.store.query(query)]

    # pylint: disable=too-many-arguments,too-many-locals
    def modify(
        self,
        target: EntryId | Description,
        maybe_description: Optional[Description],
        maybe_identity: Optional[Identity],
        maybe_plaintext: Optional[Plaintext],
        maybe_meta: Optional[Metadata],
    ) -> None:
        """Modify an existing entry.

        Args:
            target: The entry to modify.
            maybe_description: The new description of the entry.
            maybe_identity: The new identity of the entry.
            maybe_plaintext: The new plaintext of the entry.
            maybe_meta: The new metadata of the entry.
        """
        query = Query(entry_id=target) if isinstance(target, EntryId) else Query(description=target)

        query_results = self.store.query(query)
        query_results_len = len(query_results)

        if query_results_len == 0:
            raise ValueError(f"No entries match {target}")

        if query_results_len != 1:
            raise ValueError(f"Multiple entries match {target}")

        entry = query_results[0]
        description = maybe_description if maybe_description is not None else entry.description
        identity = maybe_identity if maybe_identity is not None else entry.identity
        ciphertext = self.codec.encode(maybe_plaintext) if maybe_plaintext is not None else entry.ciphertext
        meta = maybe_meta if maybe_meta is not None else entry.meta

        timestamp = Timestamp.now()
        entry_id = EntryId.generate(self.codec.key_id, timestamp, description, identity)

        new_entry = Entry(
            entry_id=entry_id,
            key_id=self.codec.key_id,
            timestamp=timestamp,
            description=description,
            identity=identity,
            ciphertext=ciphertext,
            meta=meta,
        )

        self.store.put(new_entry)
        self.store.remove(entry)

    def remove(self, target: EntryId | Description) -> None:
        """Remove an existing entry.

        Args:
            target: The entry to remove.
        """
        query = Query(entry_id=target) if isinstance(target, EntryId) else Query(description=target)

        query_results = self.store.query(query)
        query_results_len = len(query_results)

        if query_results_len == 0:
            raise ValueError(f"No entries match {target}")

        if query_results_len != 1:
            raise ValueError(f"Multiple entries match {target}")

        entry = query_results[0]
        self.store.remove(entry)

    def dump(self) -> list[Entry]:
        """Dump all entries.

        Returns:
            A list of all entries in the store.
        """
        return self.store.select_all()
