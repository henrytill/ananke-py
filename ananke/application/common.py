import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence, cast

from .. import data
from ..cipher import ArmoredCiphertext, Plaintext
from ..cipher.gpg import Text
from ..data import Description, Dictable, EntryId, Identity, Metadata, Record

type Target = EntryId | Description


class NoEntries(ValueError):
    """Signals that no entries match a given query"""


class MultipleEntries(ValueError):
    """Signals that multiple entries match a given query"""


class Application(ABC):
    """The main application class"""

    @abstractmethod
    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Identity | None = None,
        maybe_meta: Metadata | None = None,
    ) -> None:
        """Add a new entry.

        Args:
            description: The description of the entry.
            plaintext: The plaintext of the entry.
            maybe_identity: The identity of the entry.
            maybe_meta: The metadata of the entry.
        """

    @abstractmethod
    def lookup(
        self,
        description: Description,
        maybe_identity: Identity | None = None,
    ) -> list[Record]:
        """Lookup the plaintexts of the matching entries.

        Searches for entries that match the provided description and identity,
        and returns the plaintexts of the matching entries.

        Args:
            description: The description to search for.
            maybe_identity: The identity to search for.

        Returns:
            A list of the matching records.
        """

    @abstractmethod
    def modify(
        self,
        target: Target,
        maybe_description: Description | None,
        maybe_identity: Identity | None,
        maybe_plaintext: Plaintext | None,
        maybe_meta: Metadata | None,
    ) -> None:
        """Modify an existing entry.

        Args:
            target: The entry to modify.
            maybe_description: The new description of the entry.
            maybe_identity: The new identity of the entry.
            maybe_plaintext: The new plaintext of the entry.
            maybe_meta: The new metadata of the entry.
        """

    @abstractmethod
    def remove(self, target: Target) -> None:
        """Remove an existing entry.

        Args:
            target: The entry to remove.
        """

    @abstractmethod
    def import_entries(self, path: Path) -> None:
        """Import entries from a JSON file.

        Args:
            path: The path to the JSON file.
        """

    @abstractmethod
    def export_entries(self, path: Path) -> None:
        """Export entries to a JSON file.

        Args:
            path: The path to the JSON file.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""


@dataclass(frozen=True)
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

    entry_id: EntryId | None = None
    description: Description | None = None
    identity: Identity | None = None
    meta: Metadata | None = None

    def is_empty(self) -> bool:
        """Returns 'true' if all fields are 'None'."""
        return self.entry_id is None and self.description is None and self.identity is None and self.meta is None


class QueryMatcher:
    """A query matcher.

    This class is used to filter entries.
    """

    def __init__(self, query: Query) -> None:
        self.query = query

    def match_description(self, description: Description) -> bool:
        """Returns True if the description matches the query."""
        if self.query.description is None:
            return True
        return self.query.description.lower() in description.lower()

    def match_identity(self, maybe_identity: Identity | None) -> bool:
        """Returns True if the identity matches the query."""
        if self.query.identity is None:
            return True
        if maybe_identity is None:
            return False
        return self.query.identity.lower() in maybe_identity.lower()


class EntryLike(Protocol):
    """A protocol for objects that have entry_id and description fields."""

    @property
    def entry_id(self) -> EntryId:
        """Get the unique identifier for the entry."""
        ...

    @property
    def description(self) -> Description:
        """Get the description of the entry."""
        ...


def target_matches(target: Target, entry: EntryLike) -> bool:
    """Match target against entry"""
    if isinstance(target, EntryId):
        return target == entry.entry_id
    return target == entry.description


def find_one[T: EntryLike](target: Target, entries: Sequence[T]) -> int:
    """Returns the index of the single entry matching target.

    Args:
        target: The entry to find.
        entries: The entries to search.

    Returns:
        The index of the matching entry.

    Raises:
        NoEntries: If no entries match the target.
        MultipleEntries: If more than one entry matches the target.
    """
    idxs = [i for i, entry in enumerate(entries) if target_matches(target, entry)]

    if not idxs:
        raise NoEntries(f"No entries match {target}")

    if len(idxs) > 1:
        raise MultipleEntries(f"Multiple entries match {target}")

    return idxs[0]


def _read_json[T: Dictable](cls: type[T], s: str) -> list[T]:
    """Reads objects from a JSON string"""
    parsed = json.loads(s, object_hook=data.remap_keys_camel_to_snake)
    if not isinstance(parsed, list):
        raise TypeError("Expected a list")
    ret: list[T] = []
    for item in cast(list[object], parsed):
        if not isinstance(item, dict):
            raise TypeError("Expected a dictionary")
        ret.append(cls.from_dict(cast(dict[str, Any], item)))
    return ret


def read[T: Dictable](cls: type[T], path: Path, cipher: Text | None = None) -> list[T]:
    """Reads objects from a JSON file"""
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    text = path.read_text(encoding="utf-8")
    json_str = text if cipher is None else cipher.decrypt(ArmoredCiphertext(text)).value
    return _read_json(cls, json_str)


def write[T: Dictable](path: Path, writes: Sequence[T], cipher: Text | None = None) -> None:
    """Writes entries to a JSON file"""
    dicts: list[dict[str, str]] = [data.remap_keys_snake_to_camel(w.to_dict()) for w in writes]
    json_str = json.dumps(dicts, indent=2)
    text = json_str if cipher is None else cipher.encrypt(Plaintext(json_str))
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(text, encoding="utf-8")
