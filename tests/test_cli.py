"""Test the 'cli' module."""
import json
import os
import unittest
import unittest.mock
from typing import TypedDict

from tartarus import cli, data
from tartarus.codec import GpgCodec
from tartarus.config import ConfigBuilder, OsFamily
from tartarus.data import Description, Entry, Identity, Plaintext
from tartarus.store import InMemoryStore


class TestLookup(unittest.TestCase):
    """Test the lookup function."""

    def setUp(self):
        env = {
            'TARTARUS_DATA_DIR': './example',
            'TARTARUS_KEY_ID': '371C136C',
        }
        config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        with open(config.data_file, 'r', encoding='utf-8') as file:
            json_data = file.read()
        entries = [
            Entry.from_dict(entry) for entry in json.loads(json_data, object_hook=data.remap_keys_camel_to_snake)
        ]
        self.store = InMemoryStore.from_entries(entries)
        self.codec = GpgCodec(config.key_id)
        os.environ['GNUPGHOME'] = './example/gnupg'

    class TestEntry(TypedDict):
        """A type hint class for the test data."""

        description: Description
        identity: Identity
        plaintexts: list[Plaintext]

    def test_lookup(self):
        """Test the lookup function against the example data."""

        test_cases: list[TestLookup.TestEntry] = [
            {
                'description': Description('https://www.foomail.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('ASecretPassword')],
            },
            {
                'description': Description('https://www.bazbank.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('AnotherSecretPassword')],
            },
            {
                'description': Description('https://www.barphone.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('YetAnotherSecretPassword')],
            },
            {
                'description': Description('www'),
                'identity': Identity('quux'),
                'plaintexts': [
                    Plaintext('ASecretPassword'),
                    Plaintext('AnotherSecretPassword'),
                    Plaintext('YetAnotherSecretPassword'),
                ],
            },
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                actual = cli.lookup(self.store, self.codec, test_case['description'], test_case['identity'])
                self.assertEqual(test_case['plaintexts'], actual)


if __name__ == '__main__':
    unittest.main()
