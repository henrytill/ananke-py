"""The Cipher protocol."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..data import Ciphertext, KeyId

T = TypeVar("T")


# pylint: disable=unnecessary-pass
class Cipher(ABC, Generic[T]):
    """The Cipher protocol."""

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
    def encrypt(self, obj: T) -> Ciphertext:
        """Encrypts an object into a Ciphertext.

        Args:
            obj: The object to encrypt.

        Returns:
            The encrypted Ciphertext.

        Raises:
            ValueError: If the object could not be encrypted."""
        pass

    @abstractmethod
    def decrypt(self, ciphertext: Ciphertext) -> T:
        """Decrypts a Ciphertext into an object.

        Args:
            ciphertext: The Ciphertext to decrypt.

        Returns:
            The decrypted object.

        Raises:
            ValueError: If the Ciphertext could not be decrypted.
        """
        pass
