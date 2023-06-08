from collections import defaultdict

from ..data import Description, Entry, KeyId
from .abstract_store import AbstractStore, Query


class EntryMap(defaultdict[Description, set[Entry]]):
    def __init__(self):
        super().__init__(set)

    def add(self, entry: Entry) -> None:
        self.get(entry.description, set()).add(entry)

    def discard(self, entry: Entry) -> None:
        self.get(entry.description, set()).discard(entry)


class InMemoryQuery(Query):
    def __init__(self, query: Query):
        """
        Creates a query for filtering entries in memory.

        Args:
            query: The query to filter by.

        Returns:
            A query for filtering entries in memory.
        """
        super().__init__(query.id, query.description, query.identity, query.meta)

    def match_id(self, entry: Entry) -> bool:
        if self.id is None:
            return True
        return self.id == entry.id

    def match_description(self, description: Description) -> bool:
        if self.description is None:
            return True
        return self.description.lower() in description.lower()

    def match_identity(self, entry: Entry) -> bool:
        if self.identity is None:
            return True
        if entry.identity is None:
            return False
        return self.identity.lower() in entry.identity.lower()

    def match_meta(self, entry: Entry) -> bool:
        if self.meta is None:
            return True
        if entry.meta is None:
            return False
        return self.meta.lower() in entry.meta.lower()


class InMemoryStore(AbstractStore):
    """
    InMemoryStore is an implementation of the AbstractStore interface that stores data in memory.
    """

    def __init__(self):
        self.storage = EntryMap()

    def put(self, entry: Entry) -> None:
        self.storage.add(entry)

    def remove(self, entry: Entry) -> None:
        self.storage.discard(entry)

    def query(self, query: Query) -> list[Entry]:
        query = InMemoryQuery(query)
        return [
            entry
            for description, entries in self.storage.items()
            if query.match_description(description)
            for entry in entries
            if (query.match_id(entry) and query.match_identity(entry) and query.match_meta(entry))
        ]

    def select_all(self) -> list[Entry]:
        return [entry for entries in self.storage.values() for entry in entries]

    def get_count(self) -> int:
        return sum(len(entries) for entries in self.storage.values())

    def get_count_of_key_id(self, key_id: KeyId) -> int:
        return sum(entry.key_id == key_id for entries in self.storage.values() for entry in entries)
