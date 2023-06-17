"""An abstract codec."""
from abc import ABC, abstractmethod

from ..data import Ciphertext, KeyId, Plaintext


class AbstractCodec(ABC):
    """An abstract codec.

    This class is used to cryptographically encode Plaintexts and decode Ciphertexts.
    """

    @property
    @abstractmethod
    def key_id(self) -> KeyId:
        """Returns the cryptographic key used by the codec"""

    @key_id.setter
    @abstractmethod
    def key_id(self, key_id: KeyId) -> None:
        """Sets the cryptographic key used by the codec"""

    @abstractmethod
    def encode(self, plaintext: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encode.

        Returns:
            The encoded Ciphertext.

        Raises:
            ValueError: If the Plaintext could not be encoded.
        """

    @abstractmethod
    def decode(self, ciphertext: Ciphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The Ciphertext to decode.

        Returns:
            The decoded Plaintext.

        Raises:
            ValueError: If the Ciphertext could not be decoded.
        """
