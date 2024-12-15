"""The Cipher class."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..data import Plaintext, KeyId

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
