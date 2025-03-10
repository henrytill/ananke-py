import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence, Type, cast

from .. import data
from ..cipher import ArmoredCiphertext, Plaintext
from ..cipher.gpg import Text
from ..data import Description, Dictable, EntryId, Identity, Metadata, Record

type Target = EntryId | Description


class NoEntries(Exception):
    """Signals that no entries match a given query"""


class MultipleEntries(Exception):
    """Signals that multiple entries match a given query"""


class Application(ABC):
    """The main application class"""

    @abstractmethod
    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
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
        maybe_identity: Optional[Identity] = None,
    ) -> List[Record]:
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

    entry_id: Optional[EntryId] = None
    description: Optional[Description] = None
    identity: Optional[Identity] = None
    meta: Optional[Metadata] = None

    def is_empty(self) -> bool:
        """Returns 'true' if all fields are 'None'."""
        return self.entry_id is None and self.description is None and self.identity is None and self.meta is None


class EntryLike(Protocol):
    """A protocol for objects that have entry_id and description fields."""

    @property
    def entry_id(self) -> EntryId: ...

    @property
    def description(self) -> Description: ...


def target_matches(target: Target, entry: EntryLike) -> bool:
    """Match target against entry"""
    if isinstance(target, EntryId):
        return target == entry.entry_id
    return target in entry.description


def _read_json[T: Dictable](cls: Type[T], s: str) -> List[T]:
    """Reads objects from a JSON string"""
    parsed = json.loads(s, object_hook=data.remap_keys_camel_to_snake)
    if not isinstance(parsed, list):
        raise TypeError("Expected a list")
    ret: List[T] = []
    for item in cast(List[object], parsed):
        if not isinstance(item, dict):
            raise TypeError("Expected a dictionary")
        ret.append(cls.from_dict(cast(Dict[str, Any], item)))
    return ret


def read[T: Dictable](cls: Type[T], path: Path, cipher: Optional[Text] = None) -> List[T]:
    """Reads objects from a JSON file"""
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    text = path.read_text(encoding="utf-8")
    json_str = text if cipher is None else cipher.decrypt(ArmoredCiphertext(text)).value
    return _read_json(cls, json_str)


def write[T: Dictable](path: Path, writes: Sequence[T], cipher: Optional[Text] = None) -> None:
    """Writes entries to a JSON file"""
    dicts: List[Dict[str, str]] = [data.remap_keys_snake_to_camel(w.to_dict()) for w in writes]
    json_str = json.dumps(dicts, indent=2)
    text = json_str if cipher is None else cipher.encrypt(Plaintext(json_str))
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(text, encoding="utf-8")
