import datetime
import unittest

from tartarus.data import Ciphertext, Description, Entry, Id, Identity, KeyId, Metadata
from tartarus.store import InMemoryStore, Query


class TestInMemoryStore(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryStore()

    def test_put(self):
        entry = Entry(
            id=Id('1'),
            description=Description('test'),
            timestamp=datetime.datetime.now(),
            identity=Identity('test'),
            meta=Metadata('test'),
            ciphertext=Ciphertext(b'test'),
            key_id=KeyId('test'),
        )
        query = Query(description=entry.description)
        self.store.put(entry)
        self.assertEqual(self.store.query(query), [entry])


if __name__ == '__main__':
    unittest.main()
