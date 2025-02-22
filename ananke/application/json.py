import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from .. import data
from ..cipher import Plaintext
from ..cipher.gpg import Binary
from ..config import Backend, Config
from ..data import Description, Entry, EntryId, Identity, Metadata, Record, Timestamp
from . import common
from .common import Application, Query, Target


class JsonApplication(Application):
    """A JSON Application"""

    config: Config
    cipher: Binary
    entries: List[Entry]

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.JSON

        self.config = config
        self.cipher = Binary(self.config.key_id)
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.entries = []

        if self.config.data_file.exists():
            self.entries += _read(self.config.data_file)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
    ) -> None:
        timestamp = Timestamp.now()
        entry_id = EntryId.generate()
        ciphertext = self.cipher.encrypt(plaintext)
        entry = Entry(
            entry_id=entry_id,
            key_id=self.cipher.key_id,
            timestamp=timestamp,
            description=description,
            identity=maybe_identity,
            ciphertext=ciphertext,
            meta=maybe_meta,
        )
        self.entries.append(entry)
        _write(self.config.data_file, self.entries)

    def lookup(self, description: Description, maybe_identity: Optional[Identity] = None) -> List[Record]:
        query = Query(description=description, identity=maybe_identity)
        matcher = QueryMatcher(query)
        return [
            copy.deepcopy(entry).with_cipher(self.cipher)
            for entry in self.entries
            if matcher.match_description(entry.description) and matcher.match_identity(entry)
        ]

    def modify(
        self,
        target: Target,
        maybe_description: Optional[Description],
        maybe_identity: Optional[Identity],
        maybe_plaintext: Optional[Plaintext],
        maybe_meta: Optional[Metadata],
    ) -> None:
        idxs = [i for i, entry in enumerate(self.entries) if common.target_matches(target, entry)]
        idxs_len = len(idxs)

        if idxs_len == 0:
            raise ValueError(f"No entries match {target}")

        if idxs_len > 1:
            raise ValueError(f"Multiple entries match {target}")

        idx = idxs[0]

        entry = self.entries.pop(idx)
        if maybe_description is not None:
            entry.description = maybe_description
        if maybe_plaintext is not None:
            entry.ciphertext = self.cipher.encrypt(maybe_plaintext)
        if maybe_identity is not None:
            entry.identity = maybe_identity
        if maybe_meta is not None:
            entry.meta = maybe_meta
        entry.update()

        self.entries.append(entry)
        _write(self.config.data_file, self.entries)

    def remove(self, target: Target) -> None:
        idxs = [i for i, entry in enumerate(self.entries) if common.target_matches(target, entry)]
        idxs_len = len(idxs)

        if idxs_len == 0:
            raise ValueError(f"No entries match {target}")

        if idxs_len > 1:
            raise ValueError(f"Multiple entries match {target}")

        idx = idxs[0]

        del self.entries[idx]
        _write(self.config.data_file, self.entries)

    def import_entries(self, path: Optional[Path]) -> None:
        if path is None:
            return
        self.entries += _read(path)
        _write(self.config.data_file, self.entries)

    def export_entries(self, path: Optional[Path]) -> None:
        if path is None:
            return
        _write(path, self.entries)


class QueryMatcher:
    """A query matcher.

    This class is used to filter entries.

    Attributes:
        query: The query to match.
    """

    query: Query

    def __init__(self, query: Query) -> None:
        self.query = query

    def match_description(self, description: Description) -> bool:
        """Returns True if the description matches the query."""
        if self.query.description is None:
            return True
        return self.query.description.lower() in description.lower()

    def match_identity(self, entry: Entry) -> bool:
        """Returns True if the identity matches the query."""
        if self.query.identity is None:
            return True
        if entry.identity is None:
            return False
        return self.query.identity.lower() in entry.identity.lower()


def _read(path: Path) -> List[Entry]:
    """Reads entries from a JSON file"""
    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist")
    json_data = path.read_text(encoding="utf-8")
    parsed = json.loads(json_data, object_hook=data.remap_keys_camel_to_snake)
    if not isinstance(parsed, list):
        raise TypeError("Expected a list")
    ret: List[Entry] = []
    for item in cast(List[object], parsed):
        if not isinstance(item, dict):
            raise TypeError("Expected a dictionary")
        ret.append(Entry.from_dict(cast(Dict[Any, Any], item)))
    return ret


def _write(path: Path, writes: List[Entry]) -> None:
    """Writes entries to a JSON file"""
    writes.sort(key=lambda entry: entry.timestamp)
    dicts: List[Dict[str, str]] = [data.remap_keys_snake_to_camel(entry.to_dict()) for entry in writes]
    json_str = json.dumps(dicts, indent=4)
    path.write_text(json_str, encoding="utf-8")
