from abc import ABC, abstractmethod

from ..data import Ciphertext, Plaintext


class AbstractCodec(ABC):
    @abstractmethod
    def encode(self, plaintext: Plaintext) -> Ciphertext:
        """Encodes a Plaintext into a Ciphertext.

        Args:
            plaintext: The Plaintext to encode.

        Returns:
            The encoded Ciphertext.
        """
        pass

    @abstractmethod
    def decode(self, ciphertext: Ciphertext) -> Plaintext:
        """Decodes a Ciphertext into a Plaintext.

        Args:
            ciphertext: The Ciphertext to decode.

        Returns:
            The decoded Plaintext.
        """
        pass
