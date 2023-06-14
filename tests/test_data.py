"""Tests for the 'data' module."""
import base64
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
        entry_dict: EntryDict = json.loads(entry_json)
        self.assertEqual(entry_dict['Timestamp'], '2023-06-12T08:13:45.171872642Z')
        self.assertEqual(entry_dict['Id'], '4de5e12a13844ff0685b2bd51381c5501ea69b6d')
        self.assertEqual(entry_dict['KeyId'], '371C136C')
        self.assertEqual(entry_dict['Description'], 'https://www.foomail.com')
        self.assertEqual(entry_dict['Identity'], 'quux')
        self.assertEqual(entry_dict.get('Meta'), None)

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
        entry_dicts: list[EntryDict] = json.loads(entries_json)
        self.assertIsInstance(entry_dicts, list)
        self.assertEqual(len(entry_dicts), 3)
        self.assertIsInstance(entry_dicts[0], dict)

        for entry_dict in entry_dicts:
            self.assertIsInstance(entry_dict, dict)
            self.assertIn('Timestamp', entry_dict)
            self.assertIn('Id', entry_dict)
            self.assertIn('KeyId', entry_dict)
            self.assertIn('Description', entry_dict)
            self.assertIn('Identity', entry_dict)
            self.assertIn('Ciphertext', entry_dict)
            self.assertIn('Meta', entry_dict)


class TestEntry(unittest.TestCase):
    """Tests for the Entry class."""

    def test_from_dict(self):
        """An Entry can be created from a dict."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        entry_dict: EntryDict = {
            'Timestamp': '2023-06-12T08:12:08.528402975Z',
            'Id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'KeyId': '371C136C',
            'Description': 'https://www.foomail.com',
            'Identity': 'quux',
            'Ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'Meta': None,
        }

        expected_entry = Entry(
            timestamp=data.parse_timestamp(entry_dict['Timestamp']),
            entry_id=EntryId(entry_dict['Id']),
            key_id=KeyId(entry_dict['KeyId']),
            description=Description(entry_dict['Description']),
            identity=Identity(entry_dict['Identity']) if entry_dict['Identity'] is not None else None,
            ciphertext=Ciphertext(base64.b64decode(entry_dict['Ciphertext'])),
            meta=Metadata(entry_dict['Meta']) if entry_dict['Meta'] is not None else None,
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
            'Timestamp': '2023-06-12T',
            'Id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'KeyId': '371C136C',
            'Description': 'https://www.foomail.com',
            'Identity': 'quux',
            'Ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'Meta': None,
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual('Invalid timestamp format', str(context.exception))

    def test_from_dict_with_invalid_ciphertext(self):
        """An Entry cannot be created from a dict with an invalid ciphertext."""
        entry_dict: EntryDict = {
            'Timestamp': '2023-06-12T08:12:08.528402975Z',
            'Id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'KeyId': '371C136C',
            'Description': 'https://www.foomail.com',
            'Identity': 'quux',
            'Ciphertext': 'zzzzzz',
            'Meta': None,
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual('Invalid ciphertext format', str(context.exception))

    def test_missing_required_keys(self):
        """An Entry cannot be created from a dict with a missing required key."""
        # flake8: noqa: E501
        # pylint: disable=line-too-long
        base_dict = {
            'Timestamp': '2023-06-12T08:12:08.528402975Z',
            'Id': 'f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e',
            'KeyId': '371C136C',
            'Description': 'https://www.foomail.com',
            'Identity': 'quux',
            'Ciphertext': 'hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=',
            'Meta': None,
        }

        required_keys = ['Timestamp', 'Id', 'KeyId', 'Description', 'Ciphertext']

        for key in required_keys:
            with self.subTest(missing_key=key):
                entry_dict = base_dict.copy()
                del entry_dict[key]

                with self.assertRaises(ValueError) as context:
                    Entry.from_dict(entry_dict)  # type: ignore

                self.assertEqual(f'Invalid entry format: missing required key "{key}"', str(context.exception))


# pylint: disable=unused-argument, missing-function-docstring
def load_tests(loader: TestLoader, tests: TestSuite, ignore: object) -> TestSuite:
    tests.addTests(doctest.DocTestSuite(data))
    return tests


if __name__ == '__main__':
    unittest.main()
