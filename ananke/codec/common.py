"""Codec protocol."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..data import Ciphertext, KeyId

T = TypeVar("T")


# pylint: disable=unnecessary-ellipsis
class Codec(ABC, Generic[T]):
    """The codec protocol."""

    _key_id: KeyId

    @property
    def key_id(self) -> KeyId:
        """Returns the cryptographic key used by the codec"""
        return self._key_id

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        """Sets the cryptographic key used by the codec"""
        self._key_id = key_id

    @abstractmethod
    def encode(self, obj: T) -> Ciphertext:
        """Encodes an object into a Ciphertext.

        Args:
            obj: The object to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the object could not be encoded."""
        ...

    @abstractmethod
    def decode(self, ciphertext: Ciphertext) -> T:
        """Decodes a Ciphertext into an object.

        Args:
            ciphertext: The Ciphertext to decode.

        Returns:
            The decoded object.

        Raises:
            ValueError: If the Ciphertext could not be decoded.
        """
        ...
