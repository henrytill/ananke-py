import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple, TypeAlias, cast

from .. import data
from ..data import Description, Entry, EntryId, Identity, Metadata, Plaintext

Target: TypeAlias = EntryId | Description


class NoEntries(Exception):
    """Signals that no entries match a given query"""


class MultipleEntries(Exception):
    """Signals that multiple entries match a given query"""


# pylint: disable=unnecessary-pass
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
        pass

    @abstractmethod
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
        pass

    # pylint: disable=too-many-arguments
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
        pass

    @abstractmethod
    def remove(self, target: Target) -> None:
        """Remove an existing entry.

        Args:
            target: The entry to remove.
        """
        pass

    @abstractmethod
    def import_entries(self, path: Optional[Path]) -> None:
        """Import entries from a JSON file.

        Args:
            path: The path to the JSON file.
        """
        pass

    @abstractmethod
    def export_entries(self, path: Optional[Path]) -> None:
        """Export entries to a JSON file.

        Args:
            path: The path to the JSON file.
        """
        pass


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


def target_matches(target: Target, entry: Entry) -> bool:
    """Match target against entry"""
    if isinstance(target, EntryId):
        return target == entry.entry_id
    return target in entry.description


def read(path: Path) -> list[Entry]:
    """Reads entries from a JSON file"""
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    json_data = path.read_text(encoding="utf-8")
    parsed = json.loads(json_data, object_hook=data.remap_keys_camel_to_snake)
    if not isinstance(parsed, list):
        raise TypeError("Expected a list")
    ret: list[Entry] = []
    for item in cast(list[object], parsed):
        if not isinstance(item, dict):
            raise TypeError("Expected a dictionary")
        ret.append(Entry.from_dict(cast(dict[Any, Any], item)))
    return ret


def write(path: Path, writes: list[Entry]) -> None:
    """Writes entries to a JSON file"""
    writes.sort(key=lambda entry: entry.timestamp)
    dicts: list[dict[str, str]] = [data.remap_keys_snake_to_camel(entry.to_dict()) for entry in writes]
    json_str = json.dumps(dicts, indent=4)
    path.write_text(json_str, encoding="utf-8")
