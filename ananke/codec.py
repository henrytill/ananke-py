"""Codec protocol."""
from typing import Generic, Protocol, TypeVar

from .data import Ciphertext, KeyId

T = TypeVar("T")


# pylint: disable=unnecessary-ellipsis
class Codec(Protocol, Generic[T]):
    """The codec protocol."""

    @property
    def key_id(self) -> KeyId:
        """Returns the cryptographic key used by the codec"""
        ...

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        """Sets the cryptographic key used by the codec"""
        ...

    def encode(self, obj: T) -> Ciphertext:
        """Encodes an object into a Ciphertext.

        Args:
            obj: The object to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the object could not be encoded."""
        ...

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
