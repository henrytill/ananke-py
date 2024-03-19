"""The SqliteStore class."""

import sqlite3
from contextlib import closing
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Optional, cast

from ..data import Entry, KeyId
from .store import Query, Reader, Writer

CREATE_TABLE = """\
CREATE TABLE IF NOT EXISTS entries (
    id TEXT UNIQUE NOT NULL,
    keyid TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    identity TEXT,
    ciphertext TEXT NOT NULL,
    meta TEXT
)
"""


def _create_query(query: Query) -> tuple[str, dict[str, str]]:
    """Creates an SQLite Query."""
    sql = "SELECT id, keyid, timestamp, description, identity, ciphertext, meta FROM entries WHERE "
    where: list[str] = []
    parameters: dict[str, str] = {}
    if query.entry_id:
        where += ["id LIKE :id"]
        parameters["id"] = str(query.entry_id)
    if query.description:
        where += ["description LIKE :description"]
        parameters["description"] = f"%{query.description}%"
    if query.identity:
        where += ["identity LIKE :identity"]
        parameters["identity"] = query.identity
    if query.meta:
        where += ["meta LIKE :meta"]
        parameters["meta"] = query.meta
    sql += " AND ".join(where)
    return (sql, parameters)


# pylint: disable=too-few-public-methods
class SqliteConnectionReader:
    """An SQLite connection reader.

    Attributes:
        path: Path to database.
    """

    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> Connection:
        """Connects to database."""
        return sqlite3.connect(self.path)


# pylint: disable=too-few-public-methods
class NoOpWriter:
    """A no-op writer"""

    def __init__(self) -> None:
        pass

    # pylint: disable=unused-argument
    def write(self, writes: Any) -> None:
        "Writes."
        return


class SqliteStore:
    """An SQLite 3 Store

    Attributes:
        conn: An SQLite Connection.
    """

    conn: Optional[Connection]

    def __init__(self) -> None:
        self.conn = None

    def init(self, reader: Reader) -> None:
        """Initializes the store.

        Args:
            reader: The reader to use to initialize the store.
        """
        self.conn = reader.read()
        if not isinstance(self.conn, Connection):
            raise TypeError("Expected a Connection")
        cursor = self.conn.cursor()
        cursor.execute(CREATE_TABLE)

    def put(self, entry: Entry) -> None:
        """Puts an entry into the store.

        Args:
            entry: The entry to put into the store.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        sql = """\
        INSERT OR REPLACE INTO
        entries(id, keyid, timestamp, description, identity, ciphertext, meta)
        VALUES(:id, :keyid, :timestamp, :description, :identity, :ciphertext, :meta)
        """
        parameters = {
            "id": str(entry.entry_id),
            "keyid": entry.key_id,
            "timestamp": entry.timestamp.isoformat(),
            "description": entry.description,
            "identity": entry.identity,
            "ciphertext": str(entry.ciphertext.to_base64()),
            "meta": entry.meta,
        }
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(sql, parameters)

    def remove(self, entry: Entry) -> None:
        """Removes an entry from the store.

        Args:
            entry: The entry to remove from the store.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        sql = "DELETE FROM entries WHERE id = :id"
        parameters = {"id": str(entry.entry_id)}
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(sql, parameters)

    def query(self, query: Query) -> list[Entry]:
        """Queries the store.

        Args:
            query: The query to run.

        Returns:
            A list of entries that match the query.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        if query.is_empty():
            return []
        sql, parameters = _create_query(query)
        ret: list[Entry] = []
        with closing(self.conn.cursor()) as cursor:
            for row in cursor.execute(sql, parameters):
                ret.append(Entry.from_tuple(row))
        return ret

    def select_all(self) -> list[Entry]:
        """Gets all entries from the store.

        Returns:
            A list of all entries in the store.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        sql = "SELECT id, keyid, timestamp, description, identity, ciphertext, meta FROM entries"
        ret: list[Entry] = []
        with closing(self.conn.cursor()) as cursor:
            for row in cursor.execute(sql):
                ret.append(Entry.from_tuple(row))
        return ret

    def get_count(self) -> int:
        """Returns the count of all entries in the store.

        Returns:
            The count of all entries.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        sql = "SELECT count(*) FROM entries"
        ret: int = 0
        with closing(self.conn.cursor()) as cursor:
            result = cursor.execute(sql)
            (count,) = result.fetchone()
            ret = cast(int, count)
        return ret

    def get_count_of_key_id(self, key_id: KeyId) -> int:
        """Returns the count of entries for a specific key id.

        Args:
            key_id: The key id to count entries for.

        Returns:
            The count of entries for the key id.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        sql = "SELECT count(*) FROM entries WHERE keyid = :keyid"
        parameters = {"keyid": key_id}
        ret: int = 0
        with closing(self.conn.cursor()) as cursor:
            result = cursor.execute(sql, parameters)
            (count,) = result.fetchone()
            ret = cast(int, count)
        return ret

    def sync(self, writer: Writer) -> None:
        """Synchronizes the store.

        Args:
            writer: The writer to use to synchronize the store.
        """
        if not self.conn:
            raise RuntimeError("No connection")
        writer.write(None)
        self.conn.close()
