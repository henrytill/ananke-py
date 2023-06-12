"""Test the 'cli' module."""
import os
import unittest

from tartarus import cli
from tartarus.config import ConfigBuilder, OsFamily
from tartarus.data import Description, Identity, Plaintext


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

        os.environ['GNUPGHOME'] = './example/gnupg'
        self.assertEqual(cli.lookup(config, description, identity), [plaintext])


if __name__ == '__main__':
    unittest.main()
