"""The InMemoryStore class."""
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

from .. import data
from ..data import Description, Entry, KeyId
from .store import Query, Reader, Writer


class EntryMap(defaultdict[Description, set[Entry]]):
    """A map of Description to a set of Entry."""

    def __init__(self) -> None:
        super().__init__(set)

    def add(self, entry: Entry) -> None:
        """Adds an entry to the map."""
        self[entry.description].add(entry)

    def discard(self, entry: Entry) -> None:
        """Discards an entry from the map."""
        self[entry.description].discard(entry)


class InMemoryQuery(Query):
    """An in-memory query.

    This class is used to filter entries in an in-memory store.
    """

    def __init__(self, query: Query) -> None:
        super().__init__(query.entry_id, query.description, query.identity, query.meta)

    def match_id(self, entry: Entry) -> bool:
        """Returns True if the entry matches the query"""
        if self.entry_id is None:
            return True
        return self.entry_id == entry.entry_id

    def match_description(self, description: Description) -> bool:
        """Returns True if the description matches the query."""
        if self.description is None:
            return True
        return self.description.lower() in description.lower()

    def match_identity(self, entry: Entry) -> bool:
        """Returns True if the identity matches the query."""
        if self.identity is None:
            return True
        if entry.identity is None:
            return False
        return self.identity.lower() in entry.identity.lower()

    def match_meta(self, entry: Entry) -> bool:
        """Returns True if the meta matches the query."""
        if self.meta is None:
            return True
        if entry.meta is None:
            return False
        return self.meta.lower() in entry.meta.lower()


class InMemoryStore:
    """An in-memory store.

    This class is used to store entries in memory.
    """

    _storage: EntryMap
    _dirty: bool

    def __init__(self) -> None:
        self._storage = EntryMap()
        self._dirty = False

    def init(self, reader: Reader) -> None:
        """Initializes the store.

        Args:
            reader: The reader to use to initialize the store.
        """
        for entry in reader.read():
            self._storage.add(entry)

    def put(self, entry: Entry) -> None:
        """Puts an entry into the store.

        Args:
            entry: The entry to put into the store.
        """
        self._storage.add(entry)
        self._dirty = True

    def remove(self, entry: Entry) -> None:
        """Removes an entry from the store.

        Args:
            entry: The entry to remove from the store.
        """
        self._storage.discard(entry)
        self._dirty = True

    def query(self, query: Query) -> list[Entry]:
        """Queries the store.

        Args:
            query: The query to run.

        Returns:
            A list of entries that match the query.
        """
        query = InMemoryQuery(query)
        return [
            entry
            for description, entries in self._storage.items()
            if query.match_description(description)
            for entry in entries
            if query.match_id(entry) and query.match_identity(entry) and query.match_meta(entry)
        ]

    def select_all(self) -> list[Entry]:
        """Returns all entries from the store.

        Returns:
            A list of entries.
        """
        return [entry for entries in self._storage.values() for entry in entries]

    def get_count(self) -> int:
        """Returns the count of all entries in the store.

        Returns:
            The count of all entries.
        """
        return sum(len(entries) for entries in self._storage.values())

    def get_count_of_key_id(self, key_id: KeyId) -> int:
        """Returns the count of entries for a specific key id.

        Args:
            key_id: The key id to count entries for.

        Returns:
            The count of entries for the key id.
        """
        return sum(entry.key_id == key_id for entries in self._storage.values() for entry in entries)

    def sync(self, writer: Writer) -> None:
        """Synchronizes the store.

        Args:
            writer: The writer to use to synchronize the store.
        """
        if self._dirty:
            entries = self.select_all()
            writer.write(entries)
            self._dirty = False


# pylint: disable=too-few-public-methods
class JsonFileReader:
    """A JSON file reader."""

    def __init__(self, file: Path) -> None:
        self._file = file

    def read(self) -> list[Entry]:
        """Reads entries from a JSON file"""
        with open(self._file, "r", encoding="utf-8") as file:
            json_data = file.read()

        parsed = json.loads(json_data, object_hook=data.remap_keys_camel_to_snake)
        if not isinstance(parsed, list):
            raise ValueError("Expected a list")
        ret: list[Entry] = []
        for item in cast(list[object], parsed):
            if not isinstance(item, dict):
                raise ValueError("Expected a dictionary")
            ret.append(Entry.from_dict(cast(dict[Any, Any], item)))
        return ret


# pylint: disable=too-few-public-methods
class JsonFileWriter:
    """A JSON file writer."""

    def __init__(self, file: Path) -> None:
        self._file = file

    def write(self, writes: list[Entry]) -> None:
        """Writes entries to a JSON file"""
        writes.sort(key=lambda entry: entry.timestamp)
        dicts: list[dict[str, str]] = [data.remap_keys_snake_to_camel(entry.to_dict()) for entry in writes]
        with open(self._file, "w", encoding="utf-8") as file:
            json_str = json.dumps(dicts, indent=4)
            file.write(json_str)
