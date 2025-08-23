import json
from pathlib import Path
from typing import List, Optional

from .. import data
from ..cipher import ArmoredCiphertext, Plaintext
from ..cipher.gpg import Text
from ..config import Backend, Config
from ..data import Description, EntryId, Identity, Metadata, Record, SecureEntry, SecureIndexElement, Timestamp
from . import common
from .common import Application, Query, Target


class TextApplication(Application):
    """A Text Application"""

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.TEXT

        self.config = config
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.objects_dir().mkdir(parents=True, exist_ok=True)
        self.cipher = Text(self.config.key_id)
        self.elements: List[SecureIndexElement] = []
        if self.config.data_file.exists():
            self.elements += common.read(SecureIndexElement, self.config.data_file, self.cipher)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
    ) -> None:
        key_id = self.config.key_id
        entry_id = EntryId.generate()
        entry = SecureEntry(
            entry_id=entry_id,
            key_id=key_id,
            timestamp=Timestamp.now(),
            description=description,
            identity=maybe_identity,
            plaintext=plaintext,
            meta=maybe_meta,
        )
        self.write_entry(entry)
        self.elements.append(entry.to_index_element())
        self.write_index()

    def lookup(
        self,
        description: Description,
        maybe_identity: Optional[Identity] = None,
    ) -> List[Record]:
        query = Query(description=description, identity=maybe_identity)
        matcher = QueryMatcher(query)
        ret: List[Record] = []
        for elem in self.elements:
            if matcher.match_description(elem.description):
                entry = self.entry(elem.entry_id)
                if matcher.match_identity(entry.identity):
                    ret.append(entry)
        return ret

    def modify(
        self,
        target: Target,
        maybe_description: Optional[Description],
        maybe_identity: Optional[Identity],
        maybe_plaintext: Optional[Plaintext],
        maybe_meta: Optional[Metadata],
    ) -> None:
        idxs = [i for i, elem in enumerate(self.elements) if common.target_matches(target, elem)]
        idxs_len = len(idxs)

        if idxs_len == 0:
            raise ValueError(f"No entries match {target}")

        if idxs_len > 1:
            raise ValueError(f"Multiple entries match {target}")

        idx = idxs[0]

        elem = self.elements.pop(idx)
        entry = self.entry(elem.entry_id)
        if maybe_description is not None:
            entry.description = maybe_description
            elem.description = maybe_description
        if maybe_plaintext is not None:
            entry.plaintext = maybe_plaintext
        if maybe_identity is not None:
            entry.identity = maybe_identity
        if maybe_meta is not None:
            entry.meta = maybe_meta
        entry.update()

        self.write_entry(entry)
        self.elements.append(elem)
        self.write_index()

    def remove(self, target: Target) -> None:
        idxs = [i for i, elem in enumerate(self.elements) if common.target_matches(target, elem)]
        idxs_len = len(idxs)

        if idxs_len == 0:
            raise ValueError(f"No entries match {target}")

        if idxs_len > 1:
            raise ValueError(f"Multiple entries match {target}")

        idx = idxs[0]

        elem = self.elements.pop(idx)
        self.delete_entry(elem.entry_id)
        self.write_index()

    def import_entries(self, path: Path) -> None:
        secure_entries = common.read(SecureEntry, path, self.cipher)
        for entry in secure_entries:
            self.write_entry(entry)
            self.elements.append(entry.to_index_element())
        self.write_index()

    def export_entries(self, path: Path) -> None:
        secure_entries = [self.entry(elem.entry_id) for elem in self.elements]
        common.write(path, secure_entries, self.cipher)

    def clear(self) -> None:
        for elem in self.elements:
            self.delete_entry(elem.entry_id)
        self.elements.clear()
        self.write_index()

    def write_index(self) -> None:
        """Write the index to the data file."""
        common.write(self.config.data_file, self.elements, self.cipher)

    def objects_dir(self) -> Path:
        """Return the objects directory."""
        return self.config.db_dir / "objects"

    def _entry_path(self, entry_id: EntryId) -> Path:
        return self.objects_dir() / f"{entry_id}.asc"

    def entry(self, entry_id: EntryId) -> SecureEntry:
        """Read an entry from a file."""
        path = self._entry_path(entry_id)
        return _read(path, self.cipher)

    def write_entry(self, entry: SecureEntry) -> None:
        """Write an entry to a file."""
        path = self._entry_path(entry.entry_id)
        plaintext = Plaintext(json.dumps(entry.to_dict(), indent=2))
        _write(path, plaintext, self.cipher)

    def delete_entry(self, entry_id: EntryId) -> None:
        """Delete an entry."""
        path = self._entry_path(entry_id)
        path.unlink()


def _read(path: Path, cipher: Text) -> SecureEntry:
    """Read a SecureEntry from a file."""
    blob = path.read_text()
    armored = cipher.decrypt(ArmoredCiphertext(blob))
    parsed = json.loads(str(armored), object_hook=data.remap_keys_camel_to_snake)
    return SecureEntry.from_dict(parsed)


def _write(path: Path, plaintext: Plaintext, cipher: Text) -> None:
    """Write a SecureEntry to a file."""
    armored = cipher.encrypt(plaintext)
    path.write_text(str(armored))


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

    def match_identity(self, maybe_identity: Optional[Identity]) -> bool:
        """Returns True if the identity matches the query."""
        if self.query.identity is None:
            return True
        if maybe_identity is None:
            return False
        return self.query.identity.lower() in maybe_identity.lower()
