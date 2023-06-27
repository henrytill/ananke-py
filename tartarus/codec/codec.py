"""Codec protocol."""
from typing import Protocol

from ..data import Ciphertext, KeyId, Plaintext


# pylint: disable=unnecessary-ellipsis
class Codec(Protocol):
    """The codec protocol.

    This protocol is used to cryptographically encode Plaintexts and decode Ciphertexts.
    """

    @property
    def key_id(self) -> KeyId:
        """Returns the cryptographic key used by the codec"""
        ...

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        """Sets the cryptographic key used by the codec"""
        ...

    def encode(self, plaintext: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encoded.
        """
        ...

    def decode(self, ciphertext: Ciphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The Ciphertext to decode.

        Returns:
            The decoded Plaintext.

        Raises:
            ValueError: If the Ciphertext could not be decoded.
        """
        ...
