"""Tests for the 'data' module."""
import datetime
import doctest
import json
import textwrap
import unittest
from unittest import TestLoader, TestSuite

from tartarus import data
from tartarus.data import (
    Ciphertext,
    Description,
    Entry,
    EntryDict,
    EntryId,
    Identity,
    KeyId,
    Metadata,
)


class TestParseTimestamp(unittest.TestCase):
    """Tests for the 'parse_timestamp' function."""

    def test_parse_timestamp(self):
        """Tests the 'parse_timestamp' function."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640805116Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640805),
        )

    def test_parse_timestamp_fewer_microseconds(self):
        """Tests the 'parse_timestamp' function with fewer microseconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54.640Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54, 640000),
        )

    def test_parse_timestamp_no_microseconds(self):
        """Tests the 'parse_timestamp' function with no microseconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58:54Z'),
            datetime.datetime(2023, 6, 7, 2, 58, 54),
        )

    def test_parse_timestamp_no_seconds(self):
        """Tests the 'parse_timestamp' function with no seconds."""
        self.assertEqual(
            data.parse_timestamp('2023-06-07T02:58Z'),
            datetime.datetime(2023, 6, 7, 2, 58),
        )

    def test_parse_timestamp_invalid_format(self):
        """Tests the 'parse_timestamp' function with an invalid format."""
        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54:123Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02:58:54.123.456Z')

        with self.assertRaises(ValueError):
            data.parse_timestamp('2023-06-07T02Z')


class TestEntryDict(unittest.TestCase):
    """Tests for the 'EntryDict' type."""

    def test_json_loads(self):
        """An appropriate JSON object can be deserialized into an 'EntryDict' object."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entry_json = textwrap.dedent(
            """\
            {
                "Timestamp": "2023-06-12T08:13:45.171872642Z",
                "Id": "4de5e12a13844ff0685b2bd51381c5501ea69b6d",
                "KeyId": "371C136C",
                "Description": "https://www.foomail.com",
                "Identity": "quux",
                "Ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
                "Meta": null
            }
            """
        )
        entry_dict: EntryDict = json.loads(entry_json, object_hook=data.keys_to_snake_case)
        self.assertEqual(entry_dict['timestamp'], '2023-06-12T08:13:45.171872642Z')
        self.assertEqual(entry_dict['id'], '4de5e12a13844ff0685b2bd51381c5501ea69b6d')
        self.assertEqual(entry_dict['key_id'], '371C136C')
        self.assertEqual(entry_dict['description'], 'https://www.foomail.com')
        self.assertEqual(entry_dict['identity'], 'quux')
        self.assertEqual(entry_dict.get('meta'), None)

    def test_json_loads_snake_case(self):
        """An appropriate JSON object can be deserialized into an 'EntryDict' object."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entry_json = textwrap.dedent(
            """\
            {
                "timestamp": "2023-06-12T08:13:45.171872642Z",
                "id": "4de5e12a13844ff0685b2bd51381c5501ea69b6d",
                "key_id": "371C136C",
                "description": "https://www.foomail.com",
                "identity": "quux",
                "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
                "meta": null
            }
            """
        )
        entry_dict: EntryDict = json.loads(entry_json, object_hook=data.keys_to_snake_case)
        self.assertEqual(entry_dict['timestamp'], '2023-06-12T08:13:45.171872642Z')
        self.assertEqual(entry_dict['id'], '4de5e12a13844ff0685b2bd51381c5501ea69b6d')
        self.assertEqual(entry_dict['key_id'], '371C136C')
        self.assertEqual(entry_dict['description'], 'https://www.foomail.com')
        self.assertEqual(entry_dict['identity'], 'quux')
        self.assertEqual(entry_dict.get('meta'), None)

    def test_json_loads_list(self):
        """A list of appropriate JSON objects can be deserialized into a list of 'EntryDict' objects."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entries_json = textwrap.dedent(
            """\
            [
                {   
                    "Timestamp": "2023-06-12T08:13:45.171872642Z",
                    "Id": "4de5e12a13844ff0685b2bd51381c5501ea69b6d",
                    "KeyId": "371C136C",
                    "Description": "https://www.foomail.com",
                    "Identity": "quux",
                    "Ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
                    "Meta": null
                },
                {
                    "Timestamp": "2023-06-12T08:14:19.928402975Z",
                    "Id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
                    "KeyId": "371C136C",
                    "Description": "https://www.bazbank.com",
                    "Identity": "quux",
                    "Ciphertext": "hQEMAzc/TVLd4/C8AQf/QRz4kazJvOmtlUY/raQIqDMS0raFf6Pc8dfilAHnTilxfEFP4t+/l0bLbo3yncG7iDXnlMltxqJrHxQQKbhRj2M8t214I8t26QOZ55Hw0CYs2iyh2APMZGO+CWkps7hst1WB653CSNCTEyARrhTPSkJRTpzox9I8gNHcd3Fp7QvCKOTeDaSxvmJymlsJc4cNAbC/rX3z9n39QrfZmWgeffZ3DQC72rs+Let8OHrTKUMhpyeBWaA6/Lv1X9DObOseAk9zyxVgiH76hdhE9ssMgUHMURwr0Sspw1XDVagqqQlJjNbXjQI/aQ/aW2WbSMTnzJTTUPah4fn0acmNgTYMYtJQAZeTkdpCzLLrBvhXnzmagPF+bVDJY+YtUHOZclSow3gNxPq60VA4Fpy411fA/WjI+Iwnnxsyr2Ue0/qkZTO2s1p7TWNWBl7BBkhCOUL2CX8=",
                    "Meta": null
                },
                {
                    "Timestamp": "2023-06-12T08:16:30.985240519Z",
                    "Id": "39d8363eda9253a779c7719997b1a2656af19af7",
                    "KeyId": "371C136C",
                    "Description": "https://www.barphone.com",
                    "Identity": "quux",
                    "Ciphertext": "hQEMAzc/TVLd4/C8AQgAjAWcRoFoTI6k62fHtArOe6uCyEp6TDlLY5NhGKCRWKxDqggZByPDY59KzX/IqE6UgrQmvRM1yrEGvWVSM8lq43a5m8zDLNLIWVgEv0eUH50oYeB9I2vnL04L6bMPLkCwb19oFD1PUFQ9KqsmTQXyMDHkcXhAXk3mHcki1Ven38edw38Tf6xwrf/ISCSC/wDkgse6E+1+dbsEo5aWy3WWxzAFV+kARu10Mje3U+yGMBSs0Se6E/Z+iRSkCJhwOor//7W//Y0KuKzNrc3S6D4yXXIQ7lQJ33vNPAPCC5FGMwsw/StLRShNH6DHVbAp6Ws42J/9OTexwFitGY08UAX0ENJTAXhUTUGyQ23CIVfDRcWAOdsiikE7Ss37lXjrkJM86PTGrEMmY0psSrfpahkfvnmC2BsLaVTbSqz20t8J3tl5C8nlamu7AoATtDInOJcew+XcqMo=",
                    "Meta": null
                }
            ]
            """
        )
        entry_dicts: list[EntryDict] = json.loads(entries_json, object_hook=data.keys_to_snake_case)
        self.assertIsInstance(entry_dicts, list)
        self.assertEqual(len(entry_dicts), 3)
        self.assertIsInstance(entry_dicts[0], dict)

        for entry_dict in entry_dicts:
            self.assertIsInstance(entry_dict, dict)
            self.assertIn('timestamp', entry_dict)
            self.assertIn('id', entry_dict)
            self.assertIn('key_id', entry_dict)
            self.assertIn('description', entry_dict)
            self.assertIn('identity', entry_dict)
            self.assertIn('ciphertext', entry_dict)
            self.assertIn('meta', entry_dict)


class TestEntry(unittest.TestCase):
    """Tests for the Entry class."""

    def test_from_dict(self):
        """An Entry can be created from a dict."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entry_dict: EntryDict = {
            'timestamp': '2023-06-12T08:12:08.528402975Z',
            'id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'key_id': '371C136C',
            'description': 'https://www.foomail.com',
            'identity': 'quux',
            'ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'meta': None,
        }

        expected_entry = Entry(
            timestamp=data.parse_timestamp(entry_dict['timestamp']),
            entry_id=EntryId(entry_dict['id']),
            key_id=KeyId(entry_dict['key_id']),
            description=Description(entry_dict['description']),
            identity=Identity(entry_dict['identity']) if entry_dict['identity'] is not None else None,
            ciphertext=Ciphertext.from_base64(entry_dict['ciphertext']),
            meta=Metadata(entry_dict['meta']) if entry_dict['meta'] is not None else None,
        )

        actual_entry = Entry.from_dict(entry_dict)

        self.assertEqual(expected_entry, actual_entry)

    def test_from_dict_with_invalid_dict(self):
        """An Entry cannot be created from an invalid dict."""
        with self.assertRaises(ValueError, msg='Invalid dict'):
            Entry.from_dict({})  # type: ignore

    def test_from_dict_with_invalid_timestamp(self):
        """An Entry cannot be created from a dict with an invalid timestamp."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entry_dict: EntryDict = {
            'timestamp': '2023-06-12T',
            'id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'key_id': '371C136C',
            'description': 'https://www.foomail.com',
            'identity': 'quux',
            'ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'meta': None,
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual('Invalid timestamp format', str(context.exception))

    def test_from_dict_with_invalid_ciphertext(self):
        """An Entry cannot be created from a dict with an invalid ciphertext."""
        entry_dict: EntryDict = {
            'timestamp': '2023-06-12T08:12:08.528402975Z',
            'id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'key_id': '371C136C',
            'description': 'https://www.foomail.com',
            'identity': 'quux',
            'ciphertext': 'zzzzzz',
            'meta': None,
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual('Invalid ciphertext format', str(context.exception))

    def test_missing_required_keys(self):
        """An Entry cannot be created from a dict with a missing required key."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        base_dict = {
            'timestamp': '2023-06-12T08:12:08.528402975Z',
            'id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'key_id': '371C136C',
            'description': 'https://www.foomail.com',
            'identity': 'quux',
            'ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'meta': None,
        }

        required_keys = ['timestamp', 'id', 'key_id', 'description', 'ciphertext']

        for key in required_keys:
            with self.subTest(missing_key=key):
                entry_dict = base_dict.copy()
                del entry_dict[key]

                with self.assertRaises(ValueError) as context:
                    Entry.from_dict(entry_dict)  # type: ignore

                self.assertEqual(f'Invalid entry format: missing required key "{key}"', str(context.exception))


class TestKeyConversion(unittest.TestCase):
    """Unit tests for the key conversion functions."""

    def test_camel_to_snake(self):
        """Test that camel case strings are converted to snake case correctly."""
        self.assertEqual(data.convert_to_snake('CCase'), 'c_case')
        self.assertEqual(data.convert_to_snake('CamelCase'), 'camel_case')
        self.assertEqual(data.convert_to_snake('camelCase'), 'camel_case')
        self.assertEqual(data.convert_to_snake('camel2Case'), 'camel2_case')
        self.assertEqual(data.convert_to_snake('CamelCamelCamel'), 'camel_camel_camel')
        self.assertEqual(data.convert_to_snake('Camel2Camel2Camel'), 'camel2_camel2_camel')
        self.assertEqual(data.convert_to_snake('already'), 'already')
        self.assertEqual(data.convert_to_snake('already2'), 'already2')
        self.assertEqual(data.convert_to_snake('already_2'), 'already_2')
        self.assertEqual(data.convert_to_snake('already_snake'), 'already_snake')
        self.assertEqual(data.convert_to_snake('already_snake_case'), 'already_snake_case')

    def test_keys_to_snake_case(self):
        """Test that dictionary keys are converted from camel case to snake case correctly."""
        test_dict = {'CamelCase': 1, 'camelCase': 2, 'Camel2Camel2Camel': 3, 'already_snake_case': 4}
        converted = data.keys_to_snake_case(test_dict)
        # pylint: disable=duplicate-key
        expected = {'camel_case': 1, 'camel_case': 2, 'camel2_camel2_camel': 3, 'already_snake_case': 4}
        self.assertDictEqual(converted, expected)


# pylint: disable=unused-argument, missing-function-docstring
def load_tests(loader: TestLoader, tests: TestSuite, ignore: object) -> TestSuite:
    tests.addTests(doctest.DocTestSuite(data))
    return tests


if __name__ == '__main__':
    unittest.main()
