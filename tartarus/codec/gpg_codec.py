import subprocess

from ..data import Ciphertext, KeyId, Plaintext
from .abstract_codec import AbstractCodec


class GpgCodec(AbstractCodec):
    """GpgCodec is an implementation of the AbstractCodec interface that uses GPG."""

    def __init__(self, key_id: KeyId) -> None:
        """Creates a new GpgCodec with the given KeyId.

        Args:
            key_id: The KeyId to use for encryption and decryption.
        """
        self._key_id = key_id

    @property
    def key_id(self) -> KeyId:
        return self._key_id

    @key_id.setter
    def key_id(self, key_id: KeyId) -> None:
        self._key_id = key_id

    def encode(self, plaintext: Plaintext) -> Ciphertext:
        input: bytes = plaintext.encode('utf-8')
        cmd = ['gpg', '--batch', '--encrypt', '--recipient', self.key_id]
        output: bytes = subprocess.run(cmd, input=input, capture_output=True).stdout
        return Ciphertext(output)

    def decode(self, ciphertext: Ciphertext) -> Plaintext:
        cmd = ['gpg', '--batch', '--decrypt']
        result: bytes = subprocess.run(cmd, input=ciphertext, capture_output=True).stdout
        return Plaintext(result.decode('utf-8'))
