"""Tests for the GpgCodec class."""
import os
import tempfile
import unittest
from pathlib import Path
from typing import TypedDict

from tartarus.data import Ciphertext, GpgCodec, KeyId, Plaintext


class RandomArgs(TypedDict):
    """Type hint class for the 'test_random' method."""

    length: int
    use_uppercase: bool
    use_digits: bool
    use_punctuation: bool


class TestGpgCodec(unittest.TestCase):
    """Test cases for the GpgCodec class."""

    def setUp(self) -> None:
        self.key_id = KeyId("371C136C")
        self.codec = GpgCodec(self.key_id)
        os.environ["GNUPGHOME"] = str(Path.cwd() / "example" / "gnupg")

    def test_encode_decode(self):
        """Tests the encode and decode methods."""
        test_cases = [
            "ASecretPassword",
            "AnotherSecretPassword",
            "YetAnotherSecretPassword",
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                plaintext = Plaintext(test_case)
                ciphertext = self.codec.encode(plaintext)
                self.assertIsInstance(ciphertext, Ciphertext)
                decoded_plaintext = self.codec.decode(ciphertext)
                self.assertEqual(decoded_plaintext, plaintext)

    def test_encode_decode_random(self):
        """Tests the encode and decode methods with random data."""
        test_cases: list[RandomArgs] = [
            # length = 24
            {"length": 24, "use_uppercase": True, "use_digits": True, "use_punctuation": True},
            {"length": 24, "use_uppercase": True, "use_digits": True, "use_punctuation": False},
            {"length": 24, "use_uppercase": True, "use_digits": False, "use_punctuation": True},
            {"length": 24, "use_uppercase": True, "use_digits": False, "use_punctuation": False},
            {"length": 24, "use_uppercase": False, "use_digits": True, "use_punctuation": True},
            {"length": 24, "use_uppercase": False, "use_digits": True, "use_punctuation": False},
            {"length": 24, "use_uppercase": False, "use_digits": False, "use_punctuation": True},
            {"length": 24, "use_uppercase": False, "use_digits": False, "use_punctuation": False},
            # length = 48
            {"length": 48, "use_uppercase": True, "use_digits": True, "use_punctuation": True},
            {"length": 48, "use_uppercase": True, "use_digits": True, "use_punctuation": False},
            {"length": 48, "use_uppercase": True, "use_digits": False, "use_punctuation": True},
            {"length": 48, "use_uppercase": True, "use_digits": False, "use_punctuation": False},
            {"length": 48, "use_uppercase": False, "use_digits": True, "use_punctuation": True},
            {"length": 48, "use_uppercase": False, "use_digits": True, "use_punctuation": False},
            {"length": 48, "use_uppercase": False, "use_digits": False, "use_punctuation": True},
            {"length": 48, "use_uppercase": False, "use_digits": False, "use_punctuation": False},
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                plaintext = Plaintext.random(**test_case)
                ciphertext = self.codec.encode(plaintext)
                self.assertIsInstance(ciphertext, Ciphertext)
                decoded_plaintext = self.codec.decode(ciphertext)
                self.assertEqual(decoded_plaintext, plaintext)

    def test_encode_failure(self):
        """Tests the encode method with a bogus GNUPGHOME environment variable."""
        os.environ["GNUPGHOME"] = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            self.codec.encode(Plaintext("test"))

    def test_decode_failure(self):
        """Tests the decode method with a bogus GNUPGHOME environment variable."""
        os.environ["GNUPGHOME"] = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            self.codec.decode(Ciphertext(b"test"))

    def test_key_id_getter(self) -> None:
        """Tests the key_id getter.

        This test checks that the getter of the key_id property returns the correct KeyId.
        """
        self.assertEqual(self.codec.key_id, self.key_id)

    def test_key_id_setter(self) -> None:
        """Tests the key_id setter.

        This test checks that the setter of the key_id property updates the KeyId correctly.
        """
        codec = GpgCodec(KeyId("original_key_id"))
        codec.key_id = KeyId("new_key_id")
        self.assertEqual(codec.key_id, KeyId("new_key_id"))


if __name__ == "__main__":
    unittest.main()
