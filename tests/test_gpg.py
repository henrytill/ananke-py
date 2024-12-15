"""Tests for the Binary class."""

import os
import tempfile
import unittest
from pathlib import Path

from ananke.cipher import Binary
from ananke.data import Ciphertext, KeyId, Plaintext
from tests import RandomArgs


class TestBinary(unittest.TestCase):
    """Test cases for the Binary class."""

    def setUp(self) -> None:
        self.key_id = KeyId("371C136C")
        self.cipher = Binary(self.key_id)
        os.environ["GNUPGHOME"] = str(Path.cwd() / "example" / "gnupg")

    def test_encode_decode(self) -> None:
        """Tests the encode and decode methods."""
        test_cases = [
            "ASecretPassword",
            "AnotherSecretPassword",
            "YetAnotherSecretPassword",
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                plaintext = Plaintext(test_case)
                ciphertext = self.cipher.encrypt(plaintext)
                self.assertIsInstance(ciphertext, Ciphertext)
                decoded_plaintext = self.cipher.decrypt(ciphertext)
                self.assertEqual(decoded_plaintext, plaintext)

    def test_encode_decode_random(self) -> None:
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
                ciphertext = self.cipher.encrypt(plaintext)
                self.assertIsInstance(ciphertext, Ciphertext)
                decoded_plaintext = self.cipher.decrypt(ciphertext)
                self.assertEqual(decoded_plaintext, plaintext)

    def test_encode_failure(self) -> None:
        """Tests the encode method with a bogus GNUPGHOME environment variable."""
        os.environ["GNUPGHOME"] = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            self.cipher.encrypt(Plaintext("test"))

    def test_decode_failure(self) -> None:
        """Tests the decode method with a bogus GNUPGHOME environment variable."""
        os.environ["GNUPGHOME"] = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            self.cipher.decrypt(Ciphertext(b"test"))

    def test_key_id_getter(self) -> None:
        """Tests the key_id getter.

        This test checks that the getter of the key_id property returns the correct KeyId.
        """
        self.assertEqual(self.cipher.key_id, self.key_id)

    def test_key_id_setter(self) -> None:
        """Tests the key_id setter.

        This test checks that the setter of the key_id property updates the KeyId correctly.
        """
        cipher = Binary(KeyId("original_key_id"))
        cipher.key_id = KeyId("new_key_id")
        self.assertEqual(cipher.key_id, KeyId("new_key_id"))

    def test_suggest_key(self) -> None:
        """Tests the suggest_key method."""
        expected = self.key_id
        actual = self.cipher.suggest_key()
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
