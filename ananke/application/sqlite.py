import sqlite3
from contextlib import closing
from pathlib import Path
from sqlite3 import Connection
from typing import Dict, List, Optional, Tuple

from ..cipher.gpg import Binary
from ..config import Backend, Config
from ..data import Description, Entry, EntryId, Identity, Metadata, Plaintext, Timestamp
from . import common
from .common import Application, Query, Target

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS entries (
    id TEXT PRIMARY KEY NOT NULL,
    keyid TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    identity TEXT,
    ciphertext TEXT NOT NULL,
    meta TEXT
)
"""


class SqliteApplication(Application):
    """A SQLite Application"""

    config: Config
    cipher: Binary
    connection: Connection

    def __init__(self, config: Config) -> None:
        assert config.backend == Backend.SQLITE

        self.config = config
        self.cipher = Binary(self.config.key_id)
        self.config.data_file.parent.mkdir(parents=True)
        self.connection = sqlite3.connect(config.data_file)

        with closing(self.connection.cursor()) as cursor:
            cursor.execute(CREATE_TABLE)

    def close(self) -> None:
        """Closes the database connection"""
        self.connection.close()

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
        sql, parameters = _create_insert(entry)
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql, parameters)
        self.connection.commit()

    def lookup(
        self, description: Description, maybe_identity: Optional[Identity] = None
    ) -> List[Tuple[Entry, Plaintext]]:
        query = Query(description=description, identity=maybe_identity)
        sql, parameters = _create_query(query)
        ret: List[Tuple[Entry, Plaintext]] = []
        with closing(self.connection.cursor()) as cursor:
            for row in cursor.execute(sql, parameters):
                entry = Entry.from_tuple(row)
                ret.append((entry, self.cipher.decrypt(entry.ciphertext)))
        return ret

    # pylint: disable=too-many-arguments
    def modify(
        self,
        target: Target,
        maybe_description: Optional[Description],
        maybe_identity: Optional[Identity],
        maybe_plaintext: Optional[Plaintext],
        maybe_meta: Optional[Metadata],
    ) -> None:
        query = Query(entry_id=target) if isinstance(target, EntryId) else Query(description=target)
        sql, parameters = _create_query(query)
        entries: List[Entry] = []
        with closing(self.connection.cursor()) as cursor:
            for row in cursor.execute(sql, parameters):
                entries.append(Entry.from_tuple(row))

            entries_len = len(entries)

            if entries_len == 0:
                raise ValueError(f"No entries match {target}")

            if entries_len > 1:
                raise ValueError(f"Multiple entries match {target}")

            entry: Entry = entries[0]
            if maybe_description is not None:
                entry.description = maybe_description
            if maybe_plaintext is not None:
                entry.ciphertext = self.cipher.encrypt(maybe_plaintext)
            if maybe_identity is not None:
                entry.identity = maybe_identity
            if maybe_meta is not None:
                entry.meta = maybe_meta
            entry.update()

            sql, parameters = _create_update(target, entry)
            cursor.execute(sql, parameters)

        self.connection.commit()

    def remove(self, target: Target) -> None:
        if isinstance(target, EntryId):
            sql = "DELETE FROM entries WHERE id = :id"
            parameters = {"id": str(target)}
        else:
            sql = "DELETE FROM entries WHERE description = :description"
            parameters = {"description": str(target)}
        with closing(self.connection.cursor()) as cursor:
            cursor.execute(sql, parameters)
        self.connection.commit()

    def import_entries(self, path: Optional[Path]) -> None:
        if path is None:
            return
        entries: List[Entry] = common.read(path)
        with closing(self.connection.cursor()) as cursor:
            for entry in entries:
                sql, parameters = _create_insert(entry)
                cursor.execute(sql, parameters)
        self.connection.commit()

    def export_entries(self, path: Optional[Path]) -> None:
        if path is None:
            return
        sql = "SELECT id, keyid, timestamp, description, identity, ciphertext, meta FROM entries"
        entries: List[Entry] = []
        with closing(self.connection.cursor()) as cursor:
            for row in cursor.execute(sql):
                entries.append(Entry.from_tuple(row))
        common.write(path, entries)


def _create_insert(entry: Entry) -> Tuple[str, Dict[str, Optional[str]]]:
    sql: str = """\
    INSERT OR REPLACE INTO
    entries(id, keyid, timestamp, description, identity, ciphertext, meta)
    VALUES(:id, :keyid, :timestamp, :description, :identity, :ciphertext, :meta)
    """
    parameters: Dict[str, str | None] = {
        "id": str(entry.entry_id),
        "keyid": entry.key_id,
        "timestamp": entry.timestamp.isoformat(),
        "description": entry.description,
        "identity": entry.identity,
        "ciphertext": str(entry.ciphertext.to_base64()),
        "meta": entry.meta,
    }
    return (sql, parameters)


def _create_query(query: Query) -> Tuple[str, Dict[str, str]]:
    sql = "SELECT id, keyid, timestamp, description, identity, ciphertext, meta FROM entries WHERE "
    wheres: List[str] = []
    parameters: Dict[str, str] = {}
    if query.entry_id:
        wheres += ["id LIKE :id"]
        parameters["id"] = str(query.entry_id)
    if query.description:
        wheres += ["description LIKE :description"]
        parameters["description"] = f"%{query.description}%"
    if query.identity:
        wheres += ["identity LIKE :identity"]
        parameters["identity"] = f"%{query.identity}%"
    if query.meta:
        wheres += ["meta LIKE :meta"]
        parameters["meta"] = query.meta
    sql += " AND ".join(wheres)
    return (sql, parameters)


def _create_update(target: Target, entry: Entry) -> Tuple[str, Dict[str, str]]:
    parameters: Dict[str, str] = {}

    wheres: List[str] = []
    if isinstance(target, EntryId):
        wheres += ["entries.id = :target"]
    else:
        wheres += ["entries.description LIKE :target"]
    parameters["target"] = str(target)

    sets: List[str] = []

    sets += ["timestamp = :timestamp"]
    parameters["timestamp"] = entry.timestamp.isoformat()

    sets += ["keyid = :keyid"]
    parameters["keyid"] = entry.key_id

    sets += ["description = :description"]
    parameters["description"] = entry.description

    sets += ["ciphertext = :ciphertext"]
    parameters["ciphertext"] = entry.ciphertext.to_base64()

    if entry.identity is not None:
        sets += ["identity = :identity"]
        parameters["identity"] = entry.identity
    else:
        sets += ["identity = NULL"]

    if entry.meta is not None:
        sets += ["meta = :meta"]
        parameters["meta"] = entry.meta
    else:
        sets += ["meta = NULL"]

    sets_str = ",\n".join(sets)
    wheres_str = " AND ".join(wheres)
    sql = f"""\
    UPDATE entries
    SET {sets_str}
    WHERE {wheres_str}
    """
    return (sql, parameters)
