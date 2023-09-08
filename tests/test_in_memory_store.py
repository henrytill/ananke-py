"""Tests for the 'in_memory_store' module."""
import unittest

from tartarus.data import (
    Ciphertext,
    Description,
    Entry,
    EntryId,
    Identity,
    KeyId,
    Metadata,
    Timestamp,
)
from tartarus.store import InMemoryStore, Query


class TestInMemoryStore(unittest.TestCase):
    """Tests for the 'InMemoryStore' class."""

    def setUp(self):
        self.store = InMemoryStore()

    def test_put(self):
        """Tests the 'put' method."""
        entry = Entry(
            entry_id=EntryId("1"),
            description=Description("test"),
            timestamp=Timestamp.now(),
            identity=Identity("test"),
            meta=Metadata("test"),
            ciphertext=Ciphertext(b"test"),
            key_id=KeyId("test"),
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])


if __name__ == "__main__":
    unittest.main()
