"""The InMemoryStore class."""
from collections import defaultdict

from ..data import Description, Entry, KeyId
from .abstract_store import AbstractStore, Query


class EntryMap(defaultdict[Description, set[Entry]]):
    """A map of Description to a set of Entry."""

    def __init__(self):
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

    def __init__(self, query: Query):
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


class InMemoryStore(AbstractStore):
    """An in-memory store.

    This class is used to store entries in memory.
    """

    _storage: EntryMap

    def __init__(self):
        self._storage = EntryMap()

    @classmethod
    def from_entries(cls, entries: list[Entry]) -> 'InMemoryStore':
        """Creates an in-memory store from a list of entries."""
        store = cls()
        for entry in entries:
            store.put(entry)
        return store

    def put(self, entry: Entry) -> None:
        self._storage.add(entry)

    def remove(self, entry: Entry) -> None:
        self._storage.discard(entry)

    def query(self, query: Query) -> list[Entry]:
        query = InMemoryQuery(query)
        return [
            entry
            for description, entries in self._storage.items()
            if query.match_description(description)
            for entry in entries
            if (query.match_id(entry) and query.match_identity(entry) and query.match_meta(entry))
        ]

    def select_all(self) -> list[Entry]:
        return [entry for entries in self._storage.values() for entry in entries]

    def get_count(self) -> int:
        return sum(len(entries) for entries in self._storage.values())

    def get_count_of_key_id(self, key_id: KeyId) -> int:
        return sum(entry.key_id == key_id for entries in self._storage.values() for entry in entries)
