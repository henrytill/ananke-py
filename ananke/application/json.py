import copy
from pathlib import Path
from typing import Optional, Tuple

from ..config import Backend, Config
from ..data import Description, Entry, EntryId, GpgCodec, Identity, Metadata, Plaintext, Timestamp
from . import common
from .common import Application, Query, Target


class JsonApplication(Application):
    """A JSON Application"""

    config: Config
    codec: GpgCodec
    entries: list[Entry]

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.JSON

        self.config = config
        self.codec = GpgCodec(self.config.key_id)
        self.config.data_file.parent.mkdir(parents=True)
        self.entries = []

        if self.config.data_file.exists():
            self.entries += common.read(self.config.data_file)

    def add(
        self,
        description: Description,
        plaintext: Plaintext,
        maybe_identity: Optional[Identity] = None,
        maybe_meta: Optional[Metadata] = None,
    ) -> None:
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
        self.entries.append(entry)
        common.write(self.config.data_file, self.entries)

    def lookup(
        self, description: Description, maybe_identity: Optional[Identity] = None
    ) -> list[Tuple[Entry, Plaintext]]:
        query = Query(description=description, identity=maybe_identity)
        matcher = QueryMatcher(query)
        return [
            (copy.deepcopy(entry), self.codec.decode(entry.ciphertext))
            for entry in self.entries
            if matcher.match_description(entry.description) and matcher.match_identity(entry)
        ]

    # pylint: disable=too-many-arguments
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
        entry.timestamp = Timestamp.now()
        if maybe_description is not None:
            entry.description = maybe_description
        if maybe_plaintext is not None:
            entry.ciphertext = self.codec.encode(maybe_plaintext)
        if maybe_identity is not None:
            entry.identity = maybe_identity
        if maybe_meta is not None:
            entry.meta = maybe_meta
        entry.normalize()

        self.entries.append(entry)
        common.write(self.config.data_file, self.entries)

    def remove(self, target: Target) -> None:
        idxs = [i for i, entry in enumerate(self.entries) if common.target_matches(target, entry)]
        idxs_len = len(idxs)

        if idxs_len == 0:
            raise ValueError(f"No entries match {target}")

        if idxs_len > 1:
            raise ValueError(f"Multiple entries match {target}")

        idx = idxs[0]

        del self.entries[idx]
        common.write(self.config.data_file, self.entries)

    def import_entries(self, path: Optional[Path]) -> None:
        if path is not None:
            self.entries += common.read(path)

    def export_entries(self, path: Optional[Path]) -> None:
        if path is not None:
            common.write(path, self.entries)


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
