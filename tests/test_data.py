"""Tests for the 'data' module."""
import string
import unittest
from datetime import datetime, timezone
from typing import List, LiteralString, TypedDict

from ananke import data
from ananke.data import Ciphertext, Description, Entry, EntryId, Identity, KeyId, Plaintext, Timestamp
from tests import RandomArgs


class RandomTestCase(TypedDict):
    """Type hint class for the 'test_random' method."""

    args: RandomArgs
    char_set: LiteralString


class TestTimestamp(unittest.TestCase):
    """Tests for the 'Timestamp' class."""

    def test_fromisoformat(self) -> None:
        """Tests the 'fromisoformat' method."""
        test_cases = {
            "2023-06-07T02:58:54.640805116Z": datetime(2023, 6, 7, 2, 58, 54, 640805),
            "2023-06-07T02:58:54.640Z": datetime(2023, 6, 7, 2, 58, 54, 640000),
            "2023-06-07T02:58:54Z": datetime(2023, 6, 7, 2, 58, 54),
            "2023-06-07T02:58Z": datetime(2023, 6, 7, 2, 58),
        }

        for timestamp, expected_output in test_cases.items():
            with self.subTest(timestamp=timestamp):
                expected_output = expected_output.replace(tzinfo=timezone.utc)
                actual_output = Timestamp.fromisoformat(timestamp).value
                self.assertEqual(expected_output, actual_output)

    def test_roundtrip_through_str(self) -> None:
        """Tests that a 'Timestamp' object can be roundtripped through the 'str' function."""
        test_cases = [
            "2023-06-07T02:58:54.640805Z",
            "2023-06-07T02:58:54.640000Z",
            "2023-06-07T02:58:54Z",
            "2023-06-07T02:58:00Z",
        ]

        for timestamp in test_cases:
            with self.subTest(timestamp=timestamp):
                self.assertEqual(Timestamp.fromisoformat(timestamp).isoformat(), timestamp)

    def test_inequality_with_non_timestamp(self) -> None:
        """Tests that a 'Timestamp' object is not equal to a non-'Timestamp' object."""
        self.assertNotEqual(Timestamp.now(), {})


class TestCiphertext(unittest.TestCase):
    """Tests for the 'Ciphertext' class."""

    def test_from_base64(self) -> None:
        """Tests the 'from_base64' method."""
        test_cases = {
            "aGVsbG8=": b"hello",
            "aGVsbG8gZnJvbSB0ZXN0": b"hello from test",
        }

        for ciphertext, expected_output in test_cases.items():
            with self.subTest(ciphertext=ciphertext):
                actual_output = Ciphertext.from_base64(ciphertext)
                self.assertEqual(expected_output, actual_output)

    def test_to_base64(self) -> None:
        """Tests the 'to_base64' method."""
        test_cases = {
            b"hello": "aGVsbG8=",
            b"hello from test": "aGVsbG8gZnJvbSB0ZXN0",
        }

        for plaintext, expected_output in test_cases.items():
            with self.subTest(plaintext=plaintext):
                actual_output = Ciphertext(plaintext).to_base64()
                self.assertEqual(expected_output, actual_output)

    def test_roundtrip_through_str(self) -> None:
        """Tests that a 'Ciphertext' object can be roundtripped through the 'str' function."""
        test_cases = [
            "aGVsbG8=",
            "aGVsbG8gZnJvbSB0ZXN0",
        ]

        for ciphertext in test_cases:
            with self.subTest(ciphertext=ciphertext):
                self.assertEqual(Ciphertext.from_base64(ciphertext).to_base64(), ciphertext)


class TestPlaintext(unittest.TestCase):
    """Tests for the 'Plaintext' class."""

    def test_random(self) -> None:
        """Test the 'random' method of the 'Plaintext' class."""
        test_cases: List[RandomTestCase] = [
            {
                "args": {"length": 24, "use_uppercase": True, "use_digits": True, "use_punctuation": True},
                "char_set": string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation,
            },
            {
                "args": {"length": 24, "use_uppercase": True, "use_digits": True, "use_punctuation": False},
                "char_set": string.ascii_lowercase + string.ascii_uppercase + string.digits,
            },
            {
                "args": {"length": 24, "use_uppercase": True, "use_digits": False, "use_punctuation": True},
                "char_set": string.ascii_lowercase + string.ascii_uppercase + string.punctuation,
            },
            {
                "args": {"length": 24, "use_uppercase": True, "use_digits": False, "use_punctuation": False},
                "char_set": string.ascii_lowercase + string.ascii_uppercase,
            },
            {
                "args": {"length": 24, "use_uppercase": False, "use_digits": True, "use_punctuation": True},
                "char_set": string.ascii_lowercase + string.digits + string.punctuation,
            },
            {
                "args": {"length": 24, "use_uppercase": False, "use_digits": True, "use_punctuation": False},
                "char_set": string.ascii_lowercase + string.digits,
            },
            {
                "args": {"length": 24, "use_uppercase": False, "use_digits": False, "use_punctuation": True},
                "char_set": string.ascii_lowercase + string.punctuation,
            },
            {
                "args": {"length": 24, "use_uppercase": False, "use_digits": False, "use_punctuation": False},
                "char_set": string.ascii_lowercase,
            },
        ]

        for case in test_cases:
            with self.subTest(case=case):
                actual_plaintext = Plaintext.random(**case["args"])
                for char in str(actual_plaintext):
                    self.assertIn(char, case["char_set"])

    def test_random_length(self) -> None:
        """Test the length of the output generated by the 'random' method of the 'Plaintext' class"""
        lengths = range(0, 100)

        for length in lengths:
            with self.subTest(length=length):
                self.assertEqual(len(Plaintext.random(length)), length)


class TestEntry(unittest.TestCase):
    """Tests for the Entry class."""

    def test_from_dict(self) -> None:
        """An Entry can be created from a dict."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402975Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }

        expected_entry = Entry(
            timestamp=Timestamp.fromisoformat(entry_dict["timestamp"]),
            entry_id=EntryId(entry_dict["id"]),
            key_id=KeyId(entry_dict["key_id"]),
            description=Description(entry_dict["description"]),
            identity=Identity(entry_dict["identity"]),
            ciphertext=Ciphertext.from_base64(entry_dict["ciphertext"]),
            meta=None,
        )

        actual_entry = Entry.from_dict(entry_dict)

        self.assertEqual(expected_entry, actual_entry)

    def test_from_dict_with_invalid_dict(self) -> None:
        """An Entry cannot be created from an invalid dict."""
        with self.assertRaises(ValueError):
            Entry.from_dict({})

    def test_from_dict_with_illtyped_dict_required_key(self) -> None:
        """An Entry cannot be created from an ill-typed dict."""
        entry_dict = {
            "timestamp": 0,
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }

        with self.assertRaises(TypeError):
            Entry.from_dict(entry_dict)

    def test_from_dict_with_illtyped_dict_optional_key(self) -> None:
        """An Entry cannot be created from an ill-typed dict."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402975Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
            "meta": 0,
        }

        with self.assertRaises(TypeError):
            Entry.from_dict(entry_dict)

    def test_from_dict_with_invalid_timestamp(self) -> None:
        """An Entry cannot be created from a dict with an invalid timestamp."""
        entry_dict = {
            "timestamp": "2023-06-12T",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual("Invalid timestamp format", str(context.exception))

    def test_from_dict_with_invalid_ciphertext(self) -> None:
        """An Entry cannot be created from a dict with an invalid ciphertext."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402975Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "zzzzzz",
        }

        with self.assertRaises(ValueError) as context:
            Entry.from_dict(entry_dict)

        self.assertEqual("Invalid ciphertext format", str(context.exception))

    def test_missing_required_keys(self) -> None:
        """An Entry cannot be created from a dict with a missing required key."""
        base_dict = {
            "timestamp": "2023-06-12T08:12:08.528402975Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
            "meta": None,
        }

        required_keys = ["timestamp", "id", "key_id", "description", "ciphertext"]

        for key in required_keys:
            with self.subTest(missing_key=key):
                entry_dict = base_dict.copy()
                del entry_dict[key]

                with self.assertRaises(ValueError) as context:
                    Entry.from_dict(entry_dict)

                self.assertEqual(f'Invalid entry format: missing required key "{key}"', str(context.exception))

    def test_round_trip_through_dict(self) -> None:
        """An Entry can be created from a dict and converted back to a dict."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }

        self.assertEqual(entry_dict, Entry.from_dict(entry_dict).to_dict())

    def test_inequality(self) -> None:
        """Two Entries are unequal if any of their attributes are unequal."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }

        test_cases = {
            "timestamp": "2023-06-12T08:12:08.528401Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295f",
            "key_id": "371C136D",
            "description": "https://www.foomail.net",
            "identity": "qux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQgAjAWcRoFoTI6k62fHtArOe6uCyEp6TDlLY5NhGKCRWKxDqggZByPDY59KzX/IqE6UgrQmvRM1yrEGvWVSM8lq43a5m8zDLNLIWVgEv0eUH50oYeB9I2vnL04L6bMPLkCwb19oFD1PUFQ9KqsmTQXyMDHkcXhAXk3mHcki1Ven38edw38Tf6xwrf/ISCSC/wDkgse6E+1+dbsEo5aWy3WWxzAFV+kARu10Mje3U+yGMBSs0Se6E/Z+iRSkCJhwOor//7W//Y0KuKzNrc3S6D4yXXIQ7lQJ33vNPAPCC5FGMwsw/StLRShNH6DHVbAp6Ws42J/9OTexwFitGY08UAX0ENJTAXhUTUGyQ23CIVfDRcWAOdsiikE7Ss37lXjrkJM86PTGrEMmY0psSrfpahkfvnmC2BsLaVTbSqz20t8J3tl5C8nlamu7AoATtDInOJcew+XcqMo=",
            "meta": "This is some metadata",
        }

        for key, value in test_cases.items():
            with self.subTest(key=key):
                modified_entry_dict = entry_dict.copy()
                modified_entry_dict[key] = value
                self.assertNotEqual(Entry.from_dict(entry_dict), Entry.from_dict(modified_entry_dict))

    def test_inequality_with_non_entry(self) -> None:
        """An Entry is unequal to a non-Entry."""
        entry_dict = {
            "timestamp": "2023-06-12T08:12:08.528402Z",
            "id": "f06933b9b5d7dafc2ed65e7f6f629e8b72e3295e",
            "key_id": "371C136C",
            "description": "https://www.foomail.com",
            "identity": "quux",
            "ciphertext": "hQEMAzc/TVLd4/C8AQf5AWOscf34zklI490vQKnp5tI0xA0ntYuqiof7EEolHGC9V0jOjft1eBs38SMvI4MEskjKuZR+JE/m40g9xl3oSeXYbPLDAdgP0k4P7sBznbzYotRoFxKEi1mnYi/MxBtNrjG+nttxeTWXx3EseKDQfu3lz749XScwyY5aEzO+LbjQHGzqUMcntHRmareC63Do6S3pgMio1bKTuhGl87Ijf4bfw6NARg8GlF8UDUZDLnDpaaJjxJyW17owiV0SS7IC81ETydKM9wz60xUo23ow3fpEmcUhFHUspbXfSNzh2cABIfgRDhLMlZrMyuGQr9UBjw6cxMbwuNWJ5ECCGm3n3tJKAdzBFRyudhcHPwI7fm2nrthdqTJ2l+89EuP09aJsCvo4BpmAJcwSPxkrsCqirAsgctveeu+9F1LOymY9J8JGvnUu/81kYP9HYfA=",
        }
        self.assertNotEqual(Entry.from_dict(entry_dict), {})


class TestKeyConversion(unittest.TestCase):
    """Unit tests for the key conversion functions."""

    def test_remap_keys(self) -> None:
        """Keys can be remapped in a dict."""
        test_cases: list[dict[str, dict[str, str]]] = [
            {
                "key_map": {"foo": "bar", "baz": "quux"},
                "input_dict": {"foo": "a", "baz": "b"},
                "expected_output": {"bar": "a", "quux": "b"},
            },
            {
                "key_map": {"foo": "bar", "baz": "quux"},
                "input_dict": {},
                "expected_output": {},
            },
            {
                "key_map": {},
                "input_dict": {"foo": "a", "baz": "b"},
                "expected_output": {"foo": "a", "baz": "b"},
            },
            {
                "key_map": {"foo": "bar", "baz": "quux"},
                "input_dict": {"foo": "a"},
                "expected_output": {"bar": "a"},
            },
            {
                "key_map": {"foo": "bar", "baz": "quux"},
                "input_dict": {"foo": "a", "baz": "b", "quux": "c"},
                "expected_output": {"bar": "a", "quux": "c"},
            },
        ]
        for i, test_case in enumerate(test_cases):
            with self.subTest(i=i):
                key_map = test_case["key_map"]
                input_dict = test_case["input_dict"]
                expected_output = test_case["expected_output"]
                self.assertEqual(expected_output, data.remap_keys(key_map, input_dict))


if __name__ == "__main__":
    unittest.main()
