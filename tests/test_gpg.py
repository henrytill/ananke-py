"""Tests for the Binary and Text cipher classes."""

import os
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Optional, TypeVar

from ananke.cipher import Cipher
from ananke.cipher.gpg import Binary, Text
from ananke.data import ArmoredCiphertext, Ciphertext, KeyId, Plaintext
from tests import RandomArgs

T = TypeVar("T")


@dataclass(frozen=True)
class TestCipher:
    class Inner(Generic[T], unittest.TestCase):
        """Base test class for GPG cipher implementations."""

        key_id: KeyId
        cipher: Cipher[T]

        def setUp(self) -> None:
            self.key_id = KeyId("371C136C")
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
                self.cipher.decrypt(self._create_empty_ciphertext())

        def test_key_id_getter(self) -> None:
            """Tests the key_id getter."""
            self.assertEqual(self.cipher.key_id, self.key_id)

        def test_key_id_setter(self) -> None:
            """Tests the key_id setter."""
            self.cipher.key_id = KeyId("new_key_id")
            self.assertEqual(self.cipher.key_id, KeyId("new_key_id"))

        def test_suggest_key(self) -> None:
            """Tests the suggest_key method."""
            expected = self.key_id
            actual: Optional[KeyId] = self.cipher.suggest_key()
            self.assertEqual(expected, actual)

        def _create_empty_ciphertext(self) -> T:
            """Creates an empty ciphertext of the appropriate type for testing."""
            raise NotImplementedError("Subclasses must implement this method")


class TestBinary(TestCipher.Inner[Ciphertext]):
    """Test cases for the Binary class."""

    def setUp(self) -> None:
        super().setUp()
        self.cipher = Binary(self.key_id)

    def _create_empty_ciphertext(self) -> Ciphertext:
        return Ciphertext(b"test")


class TestText(TestCipher.Inner[ArmoredCiphertext]):
    """Test cases for the Text class."""

    def setUp(self) -> None:
        super().setUp()
        self.cipher = Text(self.key_id)

    def _create_empty_ciphertext(self) -> ArmoredCiphertext:
        return ArmoredCiphertext("test")


if __name__ == "__main__":
    unittest.main()
