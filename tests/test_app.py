"""Test the 'app' module."""
import os
import unittest
from typing import Optional, Tuple, TypedDict
from unittest.mock import Mock

from tartarus.app import Application
from tartarus.codec import GpgCodec
from tartarus.config import ConfigBuilder, OsFamily
from tartarus.data import (
    Ciphertext,
    Description,
    Entry,
    EntryId,
    Identity,
    Metadata,
    Plaintext,
    Timestamp,
)
from tartarus.store import InMemoryStore, JsonFileReader


class TestApplication(unittest.TestCase):
    """Test the Application class."""

    def setUp(self):
        env = {
            'TARTARUS_DATA_DIR': './example',
            'TARTARUS_KEY_ID': '371C136C',
        }
        self.config = ConfigBuilder().with_defaults(OsFamily.POSIX, {}).with_env(env).build()

        store = InMemoryStore()
        reader = JsonFileReader(self.config.data_file)
        writer = Mock()
        self.codec = GpgCodec(self.config.key_id)

        self.application = Application(store, reader, writer, self.codec)

        os.environ['GNUPGHOME'] = './example/gnupg'

    class Lookup(TypedDict):
        """A type hint class for the test data."""

        description: Description
        identity: Optional[Identity]
        plaintexts: list[Plaintext]

    def test_lookup(self):
        """Test the lookup method against the example data."""

        # see example/data.json for the test data
        test_cases: list[TestApplication.Lookup] = [
            {
                'description': Description('https://www.foomail.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('ASecretPassword')],
            },
            {
                'description': Description('https://www.foomail.com'),
                'identity': None,
                'plaintexts': [Plaintext('ASecretPassword')],
            },
            {
                'description': Description('https://www.bazbank.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('AnotherSecretPassword')],
            },
            {
                'description': Description('https://www.bazbank.com'),
                'identity': None,
                'plaintexts': [Plaintext('AnotherSecretPassword')],
            },
            {
                'description': Description('https://www.barphone.com'),
                'identity': Identity('quux'),
                'plaintexts': [Plaintext('YetAnotherSecretPassword')],
            },
            {
                'description': Description('https://www.barphone.com'),
                'identity': None,
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
            {
                'description': Description('www'),
                'identity': None,
                'plaintexts': [
                    Plaintext('ASecretPassword'),
                    Plaintext('AnotherSecretPassword'),
                    Plaintext('YetAnotherSecretPassword'),
                ],
            },
        ]

        with self.application as app:
            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    plaintexts = [
                        plaintext for _, plaintext in app.lookup(test_case['description'], test_case['identity'])
                    ]
                    self.assertEqual(test_case['plaintexts'], plaintexts)

    class Add(TypedDict):
        """A type hint class for the test data."""

        description: Description
        identity: Optional[Identity]
        plaintext: Plaintext
        meta: Optional[Metadata]

    def test_add(self):
        """Test the add method against the example data."""

        test_cases: list[TestApplication.Add] = [
            {
                'description': Description('https://www.foonews.com'),
                'identity': Identity('quux@foomail.com'),
                'plaintext': Plaintext('FooNewsSecretPassword'),
                'meta': None,
            },
            {
                'description': Description('https://www.bazblog.com'),
                'identity': Identity('quux@foomail.com'),
                'plaintext': Plaintext('BazBlogSecretPassword'),
                'meta': Metadata('{ "foo": "bar" }'),
            },
            {
                'description': Description('https://www.barsounds.com'),
                'identity': None,
                'plaintext': Plaintext('BarSoundsSecretPassword'),
                'meta': None,
            },
            {
                'description': Description('https://www.fooblog.com'),
                'identity': None,
                'plaintext': Plaintext('FooBlogSecretPassword'),
                'meta': Metadata('{ "foo": "bar" }'),
            },
        ]

        with self.application as app:
            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    app.add(test_case['description'], test_case['plaintext'], test_case['identity'], test_case['meta'])
                    results = app.lookup(test_case['description'], test_case['identity'])
                    self.assertEqual(1, len(results))
                    entry, plaintext = results[0]
                    self.assertEqual(self.config.key_id, entry.key_id)
                    self.assertEqual(test_case['description'], entry.description)
                    self.assertEqual(test_case['identity'], entry.identity)
                    self.assertEqual(test_case['plaintext'], plaintext)
                    self.assertEqual(test_case['meta'], entry.meta)

    ModifyArgs = Tuple[
        EntryId | Description,
        Optional[Description],
        Optional[Identity],
        Optional[Plaintext],
        Optional[Metadata],
    ]

    def test_modify(self):
        """Test the modify method against the example data."""

        test_cases: list[TestApplication.ModifyArgs] = [
            (
                Description('https://www.foomail.com'),
                None,
                Identity('quuxotic'),
                None,
                None,
            ),
            (
                Description('https://www.foomail.com'),
                None,
                None,
                Plaintext('ANewSecretPasswordForFooMail'),
                None,
            ),
            (
                Description('https://www.foomail.com'),
                None,
                None,
                None,
                Metadata('{ "foo": "bar" }'),
            ),
            (
                Description('https://www.foomail.com'),
                Description('https://www.foomail.net'),
                None,
                None,
                None,
            ),
            (
                Description('https://www.bazbank.com'),
                None,
                Identity('quuxotic'),
                None,
                None,
            ),
            (
                Description('https://www.bazbank.com'),
                None,
                None,
                Plaintext('ANewSecretPasswordForBazBank'),
                None,
            ),
            (
                Description('https://www.bazbank.com'),
                None,
                None,
                None,
                Metadata('{ "foo": "bar" }'),
            ),
            (
                Description('https://www.bazbank.com'),
                Description('https://www.bazbank.net'),
                None,
                None,
                None,
            ),
        ]

        with self.application as app:
            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    target, maybe_description, maybe_identity, maybe_plaintext, maybe_meta = test_case

                    if isinstance(target, EntryId):
                        raise NotImplementedError

                    results = app.lookup(target)
                    self.assertEqual(1, len(results))
                    entry, plaintext = results[0]

                    app.modify(*test_case)

                    updated_results = app.lookup(
                        maybe_description if maybe_description is not None else target,
                        maybe_identity,
                    )
                    self.assertEqual(1, len(updated_results))
                    updated_entry, updated_plaintext = updated_results[0]

                    self.assertNotEqual(entry.entry_id, updated_entry.entry_id, 'entry_id should change')
                    self.assertNotEqual(entry.timestamp, updated_entry.timestamp, 'timestamp should change')

                    self.assertEqual(self.config.key_id, updated_entry.key_id, 'key_id should not change')
                    self.assertEqual(
                        maybe_description if maybe_description is not None else entry.description,
                        updated_entry.description,
                        'description should change if provided',
                    )
                    self.assertEqual(
                        maybe_identity if maybe_identity is not None else entry.identity,
                        updated_entry.identity,
                        'identity should change if provided',
                    )
                    self.assertEqual(
                        maybe_plaintext if maybe_plaintext is not None else plaintext,
                        updated_plaintext,
                        'plaintext should change if provided',
                    )
                    self.assertEqual(
                        maybe_meta if maybe_meta is not None else entry.meta,
                        updated_entry.meta,
                        'meta should change if provided',
                    )

    def test_modify_fails_if_no_entries_match(self):
        """Test that modify fails if no entries match."""

        target = Description('zzz')

        with self.assertRaises(ValueError) as exc:
            with self.application as app:
                app.modify(target, None, None, None, None)

        self.assertEqual(f'No entries match {target}', str(exc.exception))

    def test_modify_fails_if_multiple_entries_match(self):
        """Test that modify fails if multiple entries match."""

        target = Description('www')

        with self.assertRaises(ValueError) as exc:
            with self.application as app:
                app.modify(target, None, None, None, None)

        self.assertEqual(f'Multiple entries match {target}', str(exc.exception))

    def test_remove(self):
        """Test the remove method against the example data."""

        test_cases: list[Description | EntryId] = [
            Description('https://www.foomail.com'),
            Description('https://www.bazbank.com'),
            Description('https://www.barphone.com'),
        ]

        with self.application as app:
            for test_case in test_cases:
                with self.subTest(test_case=test_case):
                    if isinstance(test_case, EntryId):
                        raise NotImplementedError

                    results = app.lookup(test_case)
                    self.assertEqual(1, len(results))
                    entry, _ = results[0]

                    app.remove(entry.entry_id)
                    results = app.lookup(test_case)
                    self.assertEqual(0, len(results))

    def test_remove_fails_if_no_entries_match(self):
        """Test that remove fails if no entries match."""

        target = Description('zzz')

        with self.assertRaises(ValueError) as exc:
            with self.application as app:
                app.remove(target)

        self.assertEqual(f'No entries match {target}', str(exc.exception))

    def test_remove_fails_if_multiple_entries_match(self):
        """Test that remove fails if multiple entries match."""

        target = Description('www')

        with self.assertRaises(ValueError) as exc:
            with self.application as app:
                app.remove(target)

        self.assertEqual(f'Multiple entries match {target}', str(exc.exception))

    def test_dump(self):
        """Test the dump method against the example data."""

        expected_entries: list[Entry] = [
            Entry(
                timestamp=Timestamp.fromisoformat('2023-06-12T08:13:45.171872642Z'),
                key_id=self.config.key_id,
                entry_id=EntryId('4de5e12a13844ff0685b2bd51381c5501ea69b6d'),
                description=Description('https://www.foomail.com'),
                identity=Identity('quux'),
                ciphertext=Ciphertext.from_base64(
                    'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA='
                ),
                meta=None,
            ),
            Entry(
                timestamp=Timestamp.fromisoformat('2023-06-12T08:14:19.928402975Z'),
                key_id=self.config.key_id,
                entry_id=EntryId('f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e'),
                description=Description('https://www.bazbank.com'),
                identity=Identity('quux'),
                ciphertext=Ciphertext.from_base64(
                    'hQEMAzc/TVLd4/C8AQf/QRz4kazJvOmtlUY/raQIqDMS0raFf6Pc8dfilAHnTilxfEFP4t+/l0bLbo3yncG7iDXnlMltxqJrHxQQKbhRj2M8t214I8t26QOZ55Hw0CYs2iyh2APMZGO+CWkps7hst1WB653CSNCTEyARrhTPSkJRTpzox9I8gNHcd3Fp7QvCKOTeDaSxvmJymlsJc4cNAbC/rX3z9n39QrfZmWgeffZ3DQC72rs+Let8OHrTKUMhpyeBWaA6/Lv1X9DObOseAk9zyxVgiH76hdhE9ssMgUHMURwr0Sspw1XDVagqqQlJjNbXjQI/aQ/aW2WbSMTnzJTTUPah4fn0acmNgTYMYtJQAZeTkdpCzLLrBvhXnzmagPF+bVDJY+YtUHOZclSow3gNxPq60VA4Fpy411fA/WjI+Iwnnxsyr2Ue0/qkZTO2s1p7TWNWBl7BBkhCOUL2CX8='
                ),
                meta=None,
            ),
            Entry(
                timestamp=Timestamp.fromisoformat('2023-06-12T08:16:30.985240519Z'),
                key_id=self.config.key_id,
                entry_id=EntryId('39d8363eda9253a779c7719997b1a2656af19af7'),
                description=Description('https://www.barphone.com'),
                identity=Identity('quux'),
                ciphertext=Ciphertext.from_base64(
                    'hQEMAzc/TVLd4/C8AQgAjAWcRoFoTI6k62fHtArOe6uCyEp6TDlLY5NhGKCRWKxDqggZByPDY59KzX/IqE6UgrQmvRM1yrEGvWVSM8lq43a5m8zDLNLIWVgEv0eUH50oYeB9I2vnL04L6bMPLkCwb19oFD1PUFQ9KqsmTQXyMDHkcXhAXk3mHcki1Ven38edw38Tf6xwrf/ISCSC/wDkgse6E+1+dbsEo5aWy3WWxzAFV+kARu10Mje3U+yGMBSs0Se6E/Z+iRSkCJhwOor//7W//Y0KuKzNrc3S6D4yXXIQ7lQJ33vNPAPCC5FGMwsw/StLRShNH6DHVbAp6Ws42J/9OTexwFitGY08UAX0ENJTAXhUTUGyQ23CIVfDRcWAOdsiikE7Ss37lXjrkJM86PTGrEMmY0psSrfpahkfvnmC2BsLaVTbSqz20t8J3tl5C8nlamu7AoATtDInOJcew+XcqMo='
                ),
                meta=None,
            ),
        ]

        with self.application as app:
            entries = app.dump()
            self.assertEqual(len(expected_entries), len(entries))
            self.assertListEqual(expected_entries, entries)


if __name__ == '__main__':
    unittest.main()
