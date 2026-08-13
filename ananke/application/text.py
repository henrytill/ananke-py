from pathlib import Path

from ..cipher import Plaintext
from ..cipher.gpg import Text
from ..config import Backend, Config
from ..data import Description, EntryId, Identity, Metadata, Record, SecureEntry, SecureIndexElement, Timestamp
from . import common
from .common import Application, Query, QueryMatcher, Target


class TextApplication(Application):
    """A Text Application"""

    def __init__(self, config: Config) -> None:
        if config.backend != Backend.TEXT:
            raise ValueError(f"TextApplication requires the {Backend.TEXT} backend, got {config.backend}")

        self.config = config
        self.config.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.objects_dir().mkdir(parents=True, exist_ok=True)
        self.cipher = Text(self.config.key_id)
        self.elements: list[SecureIndexElement] = []
        if self.config.data_file.exists():
            self.elements += common.read(SecureIndexElement, self.config.data_file, self.cipher)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Identity | None = None,
        maybe_meta: Metadata | None = None,
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
        maybe_identity: Identity | None = None,
    ) -> list[Record]:
        query = Query(description=description, identity=maybe_identity)
        matcher = QueryMatcher(query)
        ret: list[Record] = []
        for elem in self.elements:
            if matcher.match_description(elem.description):
                entry = self.entry(elem.entry_id)
                if matcher.match_identity(entry.identity):
                    ret.append(entry)
        return ret

    def modify(
        self,
        target: Target,
        maybe_description: Description | None,
        maybe_identity: Identity | None,
        maybe_plaintext: Plaintext | None,
        maybe_meta: Metadata | None,
    ) -> None:
        elem = self.elements.pop(common.find_one(target, self.elements))
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
        elem = self.elements.pop(common.find_one(target, self.elements))
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
        return common.read_one(SecureEntry, self._entry_path(entry_id), self.cipher)

    def write_entry(self, entry: SecureEntry) -> None:
        """Write an entry to a file."""
        common.write_one(self._entry_path(entry.entry_id), entry, self.cipher)

    def delete_entry(self, entry_id: EntryId) -> None:
        """Delete an entry."""
        path = self._entry_path(entry_id)
        path.unlink()
