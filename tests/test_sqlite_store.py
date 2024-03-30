"""Tests for the 'sqlite_store' module."""

import base64
import sqlite3
import unittest
from contextlib import closing
from sqlite3 import Connection
from typing import Optional

from hypothesis import given
from hypothesis import strategies as st

from ananke.data import Ciphertext, Description, Entry, EntryId, Identity, KeyId, Metadata, Timestamp
from ananke.store import Query, SqliteStore
from ananke.store.sqlite_store import NoOpWriter

TABLE_EXISTS = """\
SELECT EXISTS
(SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'entries')
"""


def clear(conn: Optional[Connection]) -> None:
    """Clears the store."""
    if not conn:
        raise RuntimeError("No connection")
    sql = "DELETE FROM entries"
    with closing(conn.cursor()) as cursor:
        cursor.execute(sql)


# pylint: disable=too-few-public-methods
class InMemorySqliteConnectionReader:
    """An in-memory SQLite connection reader."""

    def __init__(self) -> None:
        pass

    def read(self) -> Connection:
        """Connects to database."""
        return sqlite3.connect(":memory:")


class TestSqliteStore(unittest.TestCase):
    """Tests for the 'SqliteStore' class."""

    def setUp(self) -> None:
        self.reader = InMemorySqliteConnectionReader()
        self.writer = NoOpWriter()
        self.store = SqliteStore()
        self.store.init(self.reader)

    def tearDown(self) -> None:
        super().tearDown()
        self.store.sync(self.writer)

    def test_table_exists(self) -> None:
        """Tests that the 'entries' table exits on a fresh store."""
        cursor = self.store.conn.cursor()
        result_cursor = cursor.execute(TABLE_EXISTS)
        (table_exists,) = result_cursor.fetchone()
        if not isinstance(table_exists, int):
            self.fail(f"Expected an int, got {table_exists}")
        self.assertEqual(table_exists, 1)

    def test_put(self) -> None:
        """Tests the 'put' method."""
        entry = Entry(
            entry_id=EntryId("1"),
            key_id=KeyId("test"),
            timestamp=Timestamp.now(),
            description=Description("test"),
            ciphertext=Ciphertext(b"test"),
            identity=Identity("test"),
            meta=Metadata("test"),
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])

    def test_put_no_identity(self) -> None:
        """Tests the 'put' method."""
        entry = Entry(
            entry_id=EntryId("1"),
            key_id=KeyId("test"),
            timestamp=Timestamp.now(),
            description=Description("test"),
            ciphertext=Ciphertext(b"test"),
            identity=None,
            meta=Metadata("test"),
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])

    def test_put_no_meta(self) -> None:
        """Tests the 'put' method."""
        entry = Entry(
            entry_id=EntryId("1"),
            key_id=KeyId("test"),
            timestamp=Timestamp.now(),
            description=Description("test"),
            ciphertext=Ciphertext(b"test"),
            identity=Identity("test"),
            meta=None,
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])

    def test_put_no_identity_no_meta(self) -> None:
        """Tests the 'put' method."""
        entry = Entry(
            entry_id=EntryId("1"),
            key_id=KeyId("test"),
            timestamp=Timestamp.now(),
            description=Description("test"),
            ciphertext=Ciphertext(b"test"),
            identity=None,
            meta=None,
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])

    st_entry = (
        st.fixed_dictionaries(
            {
                "id": st.text(min_size=1),
                "key_id": st.text(min_size=1),
                "timestamp": st.datetimes().map(lambda d: d.isoformat()),
                "description": st.text(min_size=1),
                "ciphertext": st.binary(min_size=32, max_size=32).map(base64.b64encode).map(str),
                "identity": st.one_of(st.text(), st.none()),
                "meta": st.one_of(st.text(), st.none()),
            }
        )
        .map(Entry.from_dict)
        .map(lambda entry: entry.normalize())
    )

    @unittest.skip("We've got uniqueness problems")
    @given(st.lists(st_entry))
    def test_roundtrip(self, entries: list[Entry]) -> None:
        """Tests the 'put' and 'query' methods."""
        clear(self.store.maybe_conn)

        for entry in entries:
            self.store.put(entry)

        for entry in entries:
            query = Query(entry_id=entry.entry_id)
            self.assertIn(entry, self.store.query(query))


if __name__ == "__main__":
    unittest.main()
