"""Test the 'cli' module."""
import json
import os
import unittest
import unittest.mock

from tartarus import cli, data
from tartarus.codec import GpgCodec
from tartarus.config import ConfigBuilder, OsFamily
from tartarus.data import Description, Entry, Identity, Plaintext
from tartarus.store import InMemoryStore


class TestLookup(unittest.TestCase):
    """Test the lookup function."""

    def test_lookup(self):
        """Test the lookup function against the example data."""
        env = {
            'TARTARUS_DATA_DIR': './example',
            'TARTARUS_KEY_ID': '371C136C',
        }

        config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()
        description = Description('https://www.foomail.com')
        identity = Identity('quux')
        plaintext = Plaintext('ASecretPassword')

        with open(config.data_file, 'r', encoding='utf-8') as file:
            json_data = file.read()

        entries: list[Entry] = [
            Entry.from_dict(entry) for entry in json.loads(json_data, object_hook=data.keys_to_snake_case)
        ]

        store = InMemoryStore.from_entries(entries)

        codec = GpgCodec(config.key_id)

        os.environ['GNUPGHOME'] = './example/gnupg'
        self.assertEqual(cli.lookup(store, codec, description, identity), [plaintext])


if __name__ == '__main__':
    unittest.main()
