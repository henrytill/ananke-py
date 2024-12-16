"""The Cipher class."""

import base64
import binascii
import secrets
import string
from abc import ABC, abstractmethod
from typing import Generic, NewType, Optional, Self, TypeVar


class Plaintext:
    """A plaintext value.

    Attributes:
        value: The plaintext value.
    """

    value: str

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Plaintext):
            return False
        return self.value.__eq__(other.value)

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return f"Plaintext({self.value!r})"

    def __len__(self) -> int:
        return self.value.__len__()

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        """Encodes the plaintext value using the specified encoding.

        Args:
            encoding: The encoding to use.
            errors: The error handling scheme to use for encoding errors.

        Returns:
            The encoded value.
        """
        return self.value.encode(encoding, errors)

    @classmethod
    def random(
        cls,
        length: int,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_punctuation: bool = False,
    ) -> Self:
        """Generates a random Plaintext of a given length.

        Args:
            length: The length of the generated string.
            use_lowercase: Whether to use lowercase letters.
            use_uppercase: Whether to use uppercase letters.
            use_digits: Whether to use digits.
            use_punctuation: Whether to use punctuation.

        Returns:
            A random Plaintext of the specified length.
        """
        chars = string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_digits:
            chars += string.digits
        if use_punctuation:
            chars += string.punctuation

        ret = "".join(secrets.choice(chars) for _ in range(length))

        return cls(ret)


class Ciphertext(bytes):
    """An encrypted value of an 'Entry'."""

    def __new__(cls, value: bytes) -> Self:
        return super().__new__(cls, value)

    @classmethod
    def from_base64(cls, value: str) -> Self:
        """Creates a Ciphertext object from a base64 encoded string.

        Args:
            value: The base64 encoded string.

        Returns:
            The Ciphertext object.

        Raises:
            ValueError: If the value is not a valid base64 encoded string.
        """
        try:
            return cls(base64.b64decode(value.encode("ascii")))
        except binascii.Error as exc:
            raise ValueError("Invalid base64 string") from exc

    def to_base64(self) -> str:
        """Encodes the Ciphertext object as a base64 string.

        Returns:
            The base64 encoded string.
        """
        return base64.b64encode(self).decode("ascii")


ArmoredCiphertext = NewType("ArmoredCiphertext", str)
"""An armored ciphertext value of an 'SecureEntry'."""


KeyId = NewType("KeyId", str)
"""A Cryptographic Key Id."""


T = TypeVar("T")


class Cipher(ABC, Generic[T]):
    """The Cipher class."""

    _key_id: KeyId

    @property
    def key_id(self) -> KeyId:
        """Returns the cryptographic key used by the cipher"""
        return self._key_id

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        """Sets the cryptographic key used by the cipher"""
        self._key_id = key_id

    @abstractmethod
    def encrypt(self, plaintext: Plaintext) -> T:
        """Encrypts a Plaintext into an object.

        Args:
            obj: The Plaintext to encrypt.

        Returns:
            The encrypted object.

        Raises:
            ValueError: If the Plaintext could not be encrypted."""

    @abstractmethod
    def decrypt(self, obj: T) -> Plaintext:
        """Decrypts an object into a Plaintext.

        Args:
            ciphertext: The object to decrypt.

        Returns:
            The decrypted Plaintext.

        Raises:
            ValueError: If the object could not be decrypted.
        """

    @staticmethod
    def suggest_key() -> Optional[KeyId]:
        """Suggests a KeyId"""
